"""Expose a DeepAgents agent through FastAPI."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid4

import httpx
from deepagents import create_deep_agent
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from langchain.agents.middleware import AgentMiddleware
from langchain_openai import ChatOpenAI
from langfuse import Langfuse, propagate_attributes
from langfuse.langchain import CallbackHandler
from langfuse.types import TraceContext
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

app = FastAPI(title="DeepAgents service integration demo")


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入")
    metadata: dict[str, str] = Field(default_factory=dict, description="业务侧补充信息")


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    trace_id: str
    thread_id: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    trace_id: str
    thread_id: str


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


def get_order_status(order_id: str) -> str:
    """Return the current status for an order id."""
    orders = {
        "A1001": "已付款，等待发货",
        "A1002": "已发货，预计明天送达",
        "A1003": "已取消，退款处理中",
    }
    return orders.get(order_id, "没有找到这个订单")


@lru_cache
def get_agent():
    return create_deep_agent(
        model=build_model(),
        tools=[get_order_status],
        system_prompt="你是订单助手。回答要短。如果需要订单状态，就调用工具查询。",
        middleware=[DisableBuiltinTools()],
    )


@lru_cache
def get_langfuse() -> Langfuse:
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        base_url=os.environ["LANGFUSE_BASE_URL"],
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
        raise HTTPException(
            status_code=400,
            detail="x-trace-id must be a UUID",
        ) from exc
    trace_id = str(trace_uuid)
    thread_id = x_thread_id or f"thread-{session_id}"
    return RequestIdentity(
        session_id=session_id,
        trace_id=trace_id,
        thread_id=thread_id,
        langfuse_trace_id=trace_uuid.hex,
    )


def build_agent_config(identity: RequestIdentity) -> dict[str, Any]:
    get_langfuse()
    langfuse_handler = CallbackHandler()
    return {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": identity.thread_id},
        "run_name": "service_integration_demo",
    }


def build_agent_input(request: ChatRequest) -> dict[str, list[dict[str, str]]]:
    return {"messages": [{"role": "user", "content": request.message}]}


def trace_metadata(identity: RequestIdentity, metadata: dict[str, str]) -> dict[str, str]:
    return {
        "example": "09_service_integration",
        "session_id": identity.session_id,
        "trace_id": identity.trace_id,
        "langfuse_trace_id": identity.langfuse_trace_id,
        "thread_id": identity.thread_id,
        **metadata,
    }


def final_answer(result: dict[str, Any]) -> str:
    return result["messages"][-1].content


@app.post("/chat", response_model=ChatResponse, responses={500: {"model": ErrorResponse}})
def chat(
    request: ChatRequest,
    x_session_id: str | None = Header(default=None),
    x_trace_id: str | None = Header(default=None),
    x_thread_id: str | None = Header(default=None),
) -> ChatResponse | JSONResponse:
    identity = resolve_identity(x_session_id, x_trace_id, x_thread_id)
    agent_input = build_agent_input(request)
    config = build_agent_config(identity)
    langfuse = get_langfuse()

    try:
        with langfuse.start_as_current_observation(
            as_type="span",
            name="service_integration_demo",
            trace_context=TraceContext(trace_id=identity.langfuse_trace_id),
            input=agent_input,
            metadata=trace_metadata(identity, request.metadata),
        ) as root_span:
            with propagate_attributes(
                session_id=identity.session_id,
                tags=["deepagents-cookbook", "service-integration"],
                trace_name="service_integration_demo",
            ):
                result = get_agent().invoke(agent_input, config=config)
            root_span.update(output={"answer": final_answer(result)})
        langfuse.flush()
        return ChatResponse(
            answer=final_answer(result),
            session_id=identity.session_id,
            trace_id=identity.trace_id,
            thread_id=identity.thread_id,
        )
    except Exception as exc:
        langfuse.flush()
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="agent_run_failed",
                message=str(exc),
                trace_id=identity.trace_id,
                thread_id=identity.thread_id,
            ).model_dump(),
        )


def sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def event_payload(identity: RequestIdentity, **data: Any) -> dict[str, Any]:
    return {"session_id": identity.session_id, "trace_id": identity.trace_id, "thread_id": identity.thread_id, **data}


def chunk_text(chunk: Any) -> str:
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    x_session_id: str | None = Header(default=None),
    x_trace_id: str | None = Header(default=None),
    x_thread_id: str | None = Header(default=None),
) -> StreamingResponse:
    identity = resolve_identity(x_session_id, x_trace_id, x_thread_id)
    agent_input = build_agent_input(request)
    config = build_agent_config(identity)
    langfuse = get_langfuse()

    async def stream():
        answer_parts: list[str] = []
        yield sse_event("request.started", event_payload(identity))

        try:
            with langfuse.start_as_current_observation(
                as_type="span",
                name="service_integration_demo",
                trace_context=TraceContext(trace_id=identity.langfuse_trace_id),
                input=agent_input,
                metadata=trace_metadata(identity, request.metadata),
            ) as root_span:
                with propagate_attributes(
                    session_id=identity.session_id,
                    tags=["deepagents-cookbook", "service-integration"],
                    trace_name="service_integration_demo",
                ):
                    async for event in get_agent().astream_events(agent_input, config=config, version="v2"):
                        event_name = event.get("event")
                        data = event.get("data", {})

                        if event_name == "on_chat_model_stream":
                            delta = chunk_text(data.get("chunk"))
                            if delta:
                                answer_parts.append(delta)
                                yield sse_event("message.delta", event_payload(identity, delta=delta))

                        if event_name == "on_tool_start":
                            yield sse_event("tool.start", event_payload(identity, tool_name=event.get("name")))

                        if event_name == "on_tool_end":
                            yield sse_event("tool.end", event_payload(identity, tool_name=event.get("name")))

                root_span.update(output={"answer": "".join(answer_parts)})
            yield sse_event("message.done", event_payload(identity, answer="".join(answer_parts)))
        except Exception as exc:
            yield sse_event(
                "error",
                event_payload(identity, code="agent_run_failed", message=str(exc)),
            )
        finally:
            langfuse.flush()

    return StreamingResponse(stream(), media_type="text/event-stream")
