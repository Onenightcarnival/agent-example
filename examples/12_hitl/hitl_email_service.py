"""Review an email draft before a service sends it."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Literal
from uuid import UUID, uuid4

import deepagents
import httpx
from deepagents import create_deep_agent
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.human_in_the_loop import InterruptOnConfig
from langchain_openai import ChatOpenAI
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langfuse.types import TraceContext
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, Interrupt
from pydantic import BaseModel, Field

BUILTIN_TOOLS = frozenset(
    {
        "write_todos",
        "ls",
        "read_file",
        "write_file",
        "edit_file",
        "glob",
        "grep",
        "execute",
        "task",
    }
)

app = FastAPI(title="DeepAgents HITL email demo")


class DraftRequest(BaseModel):
    message: str = Field(..., description="用户给 agent 的任务")
    metadata: dict[str, str] = Field(default_factory=dict, description="业务侧补充信息")


class ReviewDecision(BaseModel):
    type: Literal["approve", "edit", "reject"]
    review_id: str | None = Field(default=None, description="待审核动作 id，示例不做强校验")
    to: str | None = Field(default=None, description="edit 时填写")
    subject: str | None = Field(default=None, description="edit 时填写")
    body: str | None = Field(default=None, description="edit 时填写")
    message: str | None = Field(default=None, description="reject 时填写")


class RequestIdentity(BaseModel):
    session_id: str
    trace_id: str
    thread_id: str
    langfuse_trace_id: str


def tool_name(tool: Any) -> str | None:
    if isinstance(tool, dict):
        name = tool.get("name")
        return name if isinstance(name, str) else None
    name = getattr(tool, "name", None)
    return name if isinstance(name, str) else None


class DisableBuiltinTools(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        tools = [tool for tool in request.tools if tool_name(tool) not in BUILTIN_TOOLS]
        return handler(request.override(tools=tools))

    async def awrap_model_call(self, request, handler):
        tools = [tool for tool in request.tools if tool_name(tool) not in BUILTIN_TOOLS]
        return await handler(request.override(tools=tools))


def build_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
        http_client=httpx.Client(trust_env=False),
        extra_body={
            "thinking": {"type": "disabled"},  # DeepSeek：关闭 thinking。
            "chat_template_kwargs": {"enable_thinking": False},  # 自部署模型服务：关闭 chat template thinking。
        },
    )


def read_ticket(ticket_id: str) -> str:
    """Read a customer support ticket by id."""
    tickets = {
        "T1001": (
            "客户：lin@example.com\n"
            "问题：客户的订单 A1002 已发货，但物流页面没有更新。\n"
            "处理建议：说明订单已发货，预计明天送达。提醒客户明天再查看物流。"
        ),
        "T1002": (
            "客户：mei@example.com\n"
            "问题：客户取消了订单 A1003，询问退款时间。\n"
            "处理建议：说明退款处理中，通常 3 个工作日内原路退回。"
        ),
    }
    return tickets.get(ticket_id, "没有找到这个工单。")


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email after human approval. This demo only returns a send record."""
    return f"邮件已发送：to={to}, subject={subject}, body={body}"


def describe_email_review(tool_call: dict[str, Any], *_args: Any) -> str:
    args = tool_call["args"]
    return (
        "请审核这封邮件。确认收件人、标题和正文后再发送。\n\n"
        f"to: {args.get('to')}\n"
        f"subject: {args.get('subject')}\n"
        f"body:\n{args.get('body')}"
    )


@lru_cache
def get_checkpointer() -> MemorySaver:
    return MemorySaver()


@lru_cache
def get_langfuse() -> Langfuse:
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        base_url=os.environ["LANGFUSE_BASE_URL"],
    )


@lru_cache
def get_agent():
    email_review: InterruptOnConfig = {
        "allowed_decisions": ["approve", "edit", "reject"],
        "description": describe_email_review,
    }
    return create_deep_agent(
        model=build_model(),
        tools=[read_ticket, send_email],
        system_prompt=(
            "你是客服邮件助手。用户会让你处理工单并回复客户。"
            "需要工单信息时，先调用 read_ticket。"
            "准备好邮件后，必须调用 send_email，并把 to、subject、body 写清楚。"
            "send_email 会在服务层等待人工审核。"
            "如果发送被拒绝，告诉用户没有发送。"
        ),
        middleware=[DisableBuiltinTools()],
        checkpointer=get_checkpointer(),
        interrupt_on={"send_email": email_review},
    )


def resolve_identity(
    x_session_id: str | None,
    x_trace_id: str | None,
    x_thread_id: str | None,
) -> RequestIdentity:
    session_id = x_session_id or f"session-{uuid4().hex}"
    try:
        trace_uuid = UUID(x_trace_id) if x_trace_id else uuid4()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="x-trace-id must be a UUID") from exc
    trace_id = str(trace_uuid)
    thread_id = x_thread_id or f"thread-{session_id}"
    return RequestIdentity(
        session_id=session_id,
        trace_id=trace_id,
        thread_id=thread_id,
        langfuse_trace_id=trace_uuid.hex,
    )


def agent_config(identity: RequestIdentity) -> dict[str, Any]:
    get_langfuse()
    langfuse_handler = CallbackHandler(trace_context=TraceContext(trace_id=identity.langfuse_trace_id))
    return {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": identity.thread_id},
        "metadata": {
            "ls_integration": "deepagents",
            "versions": f"deepagents={deepagents.__version__}",
            "lc_agent_name": "hitl_email_review_demo",
        },
        "run_name": "hitl_email_review_demo",
    }


def trace_metadata(identity: RequestIdentity, metadata: dict[str, str]) -> dict[str, str]:
    return {
        "example": "12_hitl",
        "session_id": identity.session_id,
        "trace_id": identity.trace_id,
        "langfuse_trace_id": identity.langfuse_trace_id,
        "thread_id": identity.thread_id,
        **metadata,
    }


def final_answer(result: dict[str, Any]) -> str:
    return result["messages"][-1].content


def chunk_text(chunk: Any) -> str:
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def event_payload(identity: RequestIdentity, **data: Any) -> dict[str, Any]:
    return {
        "session_id": identity.session_id,
        "trace_id": identity.trace_id,
        "thread_id": identity.thread_id,
        **data,
    }


def first_interrupt(result: dict[str, Any]) -> Interrupt | None:
    interrupts = result.get("__interrupt__", [])
    return interrupts[0] if interrupts else None


def interrupt_email(interrupt: Interrupt) -> dict[str, Any]:
    request = interrupt.value
    action = request["action_requests"][0]
    return dict(action["args"])


def interrupt_from_chunk(chunk: Any) -> Interrupt | None:
    if not isinstance(chunk, dict):
        return None
    interrupts = chunk.get("__interrupt__")
    if not interrupts:
        return None
    return interrupts[0]


def is_root_graph_event(event: dict[str, Any]) -> bool:
    return event.get("name") == "LangGraph"


def resume_payload(decision: ReviewDecision) -> dict[str, Any]:
    if decision.type == "approve":
        return {"decisions": [{"type": "approve"}]}
    if decision.type == "reject":
        return {"decisions": [{"type": "reject", "message": decision.message or "人工审核拒绝发送。"}]}

    missing = [name for name in ("to", "subject", "body") if getattr(decision, name) is None]
    if missing:
        raise HTTPException(status_code=400, detail=f"edit decision missing fields: {', '.join(missing)}")
    return {
        "decisions": [
            {
                "type": "edit",
                "edited_action": {
                    "name": "send_email",
                    "args": {
                        "to": decision.to,
                        "subject": decision.subject,
                        "body": decision.body,
                    },
                },
            }
        ]
    }


@app.post("/drafts/stream")
def create_draft_stream(
    request: DraftRequest,
    x_session_id: str | None = Header(default=None),
    x_trace_id: str | None = Header(default=None),
    x_thread_id: str | None = Header(default=None),
) -> StreamingResponse:
    identity = resolve_identity(x_session_id, x_trace_id, x_thread_id)

    async def stream():
        langfuse = get_langfuse()
        yield sse_event("request.started", event_payload(identity))
        agent_input = {"messages": [{"role": "user", "content": request.message}]}
        root_span = langfuse.start_observation(
            as_type="span",
            name="hitl_email_draft",
            trace_context=TraceContext(trace_id=identity.langfuse_trace_id),
            input=agent_input,
            metadata=trace_metadata(identity, request.metadata),
        )
        output: dict[str, Any] = {}
        try:
            async for event in get_agent().astream_events(agent_input, config=agent_config(identity), version="v2"):
                event_name = event.get("event")
                data = event.get("data", {})

                if event_name == "on_chat_model_stream":
                    delta = chunk_text(data.get("chunk"))
                    if delta:
                        yield sse_event("message.delta", event_payload(identity, delta=delta))

                if event_name == "on_tool_start":
                    yield sse_event("tool.started", event_payload(identity, tool_name=event.get("name")))

                if event_name == "on_tool_end":
                    yield sse_event("tool.finished", event_payload(identity, tool_name=event.get("name")))

                interrupt = interrupt_from_chunk(data.get("chunk")) if is_root_graph_event(event) else None
                if interrupt:
                    review_payload = event_payload(
                        identity,
                        review_id=interrupt.id,
                        email=interrupt_email(interrupt),
                    )
                    output = {"status": "pending_review", **review_payload}
                    yield sse_event("review.required", review_payload)

                if event_name == "on_chain_end" and is_root_graph_event(event):
                    result = data.get("output")
                    if isinstance(result, dict) and "messages" in result:
                        answer = final_answer(result)
                        output = {"status": "completed", "answer": answer}
                        yield sse_event("message.done", event_payload(identity, answer=answer))
        except Exception as exc:
            output = {"status": "error", "message": str(exc)}
            yield sse_event("error", event_payload(identity, code="agent_run_failed", message=str(exc)))
        finally:
            if output:
                root_span.update(output=output)
            root_span.end()
            langfuse.flush()

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/reviews/stream")
def submit_review_stream(
    decision: ReviewDecision,
    x_session_id: str | None = Header(default=None),
    x_trace_id: str | None = Header(default=None),
    x_thread_id: str | None = Header(default=None),
) -> StreamingResponse:
    identity = resolve_identity(x_session_id, x_trace_id, x_thread_id)

    async def stream():
        langfuse = get_langfuse()
        yield sse_event("review.received", event_payload(identity, review_id=decision.review_id))
        command = Command(resume=resume_payload(decision))
        root_span = langfuse.start_observation(
            as_type="span",
            name="hitl_email_review",
            trace_context=TraceContext(trace_id=identity.langfuse_trace_id),
            input={"decision": decision.model_dump(exclude_none=True)},
            metadata=trace_metadata(identity, {"review_id": decision.review_id or ""}),
        )
        output: dict[str, Any] = {}
        try:
            async for event in get_agent().astream_events(command, config=agent_config(identity), version="v2"):
                event_name = event.get("event")
                data = event.get("data", {})

                if event_name == "on_chat_model_stream":
                    delta = chunk_text(data.get("chunk"))
                    if delta:
                        yield sse_event("message.delta", event_payload(identity, delta=delta))

                if event_name == "on_tool_start":
                    yield sse_event("tool.started", event_payload(identity, tool_name=event.get("name")))

                if event_name == "on_tool_end":
                    yield sse_event("tool.finished", event_payload(identity, tool_name=event.get("name")))

                interrupt = interrupt_from_chunk(data.get("chunk")) if is_root_graph_event(event) else None
                if interrupt:
                    review_payload = event_payload(
                        identity,
                        review_id=interrupt.id,
                        email=interrupt_email(interrupt),
                    )
                    output = {"status": "pending_review", **review_payload}
                    yield sse_event("review.required", review_payload)

                if event_name == "on_chain_end" and is_root_graph_event(event):
                    result = data.get("output")
                    if isinstance(result, dict) and "messages" in result:
                        answer = final_answer(result)
                        service_event = "email.cancelled" if decision.type == "reject" else "email.sent"
                        output = {"status": service_event, "answer": answer}
                        yield sse_event(service_event, event_payload(identity, answer=answer))
        except Exception as exc:
            output = {"status": "error", "message": str(exc)}
            yield sse_event("error", event_payload(identity, code="agent_resume_failed", message=str(exc)))
        finally:
            if output:
                root_span.update(output=output)
            root_span.end()
            langfuse.flush()

    return StreamingResponse(stream(), media_type="text/event-stream")
