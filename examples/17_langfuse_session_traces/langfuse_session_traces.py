"""Group multiple DeepAgents turns in one Langfuse session."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_openai import ChatOpenAI
from langfuse import Langfuse, propagate_attributes
from langfuse.api.commons.errors.not_found_error import NotFoundError
from langfuse.langchain import CallbackHandler
from langfuse.types import TraceContext
from langgraph.checkpoint.memory import MemorySaver

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

SESSION_ID = str(uuid4())
THREAD_ID = str(uuid4())
TRACE_NAME = "langfuse_session_trace_demo"
PUBLIC_API_FIELDS = "basic"


@dataclass(frozen=True)
class TurnResult:
    index: int
    message: str
    answer: str
    trace_id: str
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
    return orders.get(order_id, "没有找到这个订单。")


def build_agent():
    return create_deep_agent(
        model=build_model(),
        tools=[get_order_status],
        system_prompt=(
            "你是订单助手。回答要短。"
            "如果需要订单状态，就调用工具查询。"
            "如果用户问前文提到的订单，要从当前对话上下文里判断。"
        ),
        middleware=[DisableBuiltinTools()],
        checkpointer=MemorySaver(),
    )


def build_langfuse() -> Langfuse:
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        base_url=os.environ["LANGFUSE_BASE_URL"],
    )


def run_turn(langfuse: Langfuse, agent, index: int, message: str) -> TurnResult:
    trace_uuid = uuid4()
    trace_id = str(trace_uuid)
    langfuse_trace_id = trace_uuid.hex
    agent_input = {"messages": [{"role": "user", "content": message}]}
    handler = CallbackHandler(trace_context=TraceContext(trace_id=langfuse_trace_id))

    with langfuse.start_as_current_observation(
        as_type="span",
        name=f"{TRACE_NAME}_turn_{index}",
        trace_context=TraceContext(trace_id=langfuse_trace_id),
        input=agent_input,
        metadata={
            "example": "17_langfuse_session_traces",
            "session_id": SESSION_ID,
            "trace_id": trace_id,
            "langfuse_trace_id": langfuse_trace_id,
            "thread_id": THREAD_ID,
            "turn": str(index),
        },
    ) as root_span:
        with propagate_attributes(
            session_id=SESSION_ID,
            tags=["deepagents-cookbook", "langfuse-session"],
            trace_name=TRACE_NAME,
        ):
            result = agent.invoke(
                agent_input,
                config={
                    "callbacks": [handler],
                    "configurable": {"thread_id": THREAD_ID},
                    "run_name": f"{TRACE_NAME}_turn_{index}",
                },
            )
        answer = result["messages"][-1].content
        root_span.update(output={"answer": answer})

    return TurnResult(
        index=index,
        message=message,
        answer=answer,
        trace_id=trace_id,
        langfuse_trace_id=langfuse_trace_id,
    )


def wait_for_public_api(langfuse: Langfuse, trace_ids: list[str], timeout_seconds: int = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    missing = {UUID(trace_id).hex for trace_id in trace_ids}

    while missing and time.monotonic() < deadline:
        for trace_id in list(missing):
            try:
                trace = langfuse.api.trace.get(trace_id, fields=PUBLIC_API_FIELDS)
            except Exception:
                continue
            if getattr(trace, "id", None) == trace_id:
                missing.remove(trace_id)
        if missing:
            time.sleep(2)

    if missing:
        print(f"public api 还没返回这些 trace：{', '.join(sorted(missing))}")


def print_session_summary(langfuse: Langfuse, turns: list[TurnResult]) -> None:
    traces = langfuse.api.trace.list(
        session_id=SESSION_ID,
        name=TRACE_NAME,
        limit=20,
        fields=PUBLIC_API_FIELDS,
    )
    trace_session_ids = {trace.id: trace.session_id for trace in traces.data}

    print("\nLangfuse Public API trace sessionId:")
    for turn in turns:
        print(
            f"- turn {turn.index}: traceId={turn.trace_id}, sessionId={trace_session_ids.get(turn.langfuse_trace_id)}"
        )

    print("\nLangfuse Public API observation sessionId:")
    for turn in turns:
        try:
            observations = langfuse.api.observations.get_many(
                trace_id=turn.langfuse_trace_id,
                limit=100,
                fields=PUBLIC_API_FIELDS,
            )
        except NotFoundError as exc:
            print(f"- turn {turn.index}: 当前 Langfuse 部署不支持 v2 observations API，无法读取 sessionId")
            print(f"  error: {exc.body.get('message')}")
            continue

        session_ids = sorted({observation.session_id for observation in observations.data})
        print(f"- turn {turn.index}: {session_ids}")


def main() -> None:
    langfuse = build_langfuse()
    agent = build_agent()
    messages = [
        "查一下订单 A1002 的状态，并用一句话回复。",
        "继续刚才的会话，再查一下订单 A1003。",
        "把刚才两个订单的状态合成一句话。",
    ]

    print(f"sessionId: {SESSION_ID}")
    print(f"threadId: {THREAD_ID}")

    turns: list[TurnResult] = []
    for index, message in enumerate(messages, start=1):
        turn = run_turn(langfuse, agent, index, message)
        turns.append(turn)
        print(f"\nturn {turn.index}")
        print(f"user: {turn.message}")
        print(f"traceId: {turn.trace_id}")
        print(f"assistant: {turn.answer}")

    langfuse.flush()
    wait_for_public_api(langfuse, [turn.trace_id for turn in turns])
    print_session_summary(langfuse, turns)


if __name__ == "__main__":
    main()
