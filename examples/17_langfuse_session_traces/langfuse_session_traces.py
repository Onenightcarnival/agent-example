"""Group multiple DeepAgents turns in one Langfuse session."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_openai import ChatOpenAI
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

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
TRACE_NAME = "langfuse_session_trace_demo"


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
        system_prompt="你是订单助手。回答要短。如果需要订单状态，就调用工具查询。",
        middleware=[DisableBuiltinTools()],
    )


def build_langfuse() -> Langfuse:
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        base_url=os.environ["LANGFUSE_BASE_URL"],
    )


def run_turn(agent, index: int, message: str) -> TurnResult:
    agent_input = {"messages": [{"role": "user", "content": message}]}
    handler = CallbackHandler(public_key=os.environ["LANGFUSE_PUBLIC_KEY"])

    result = agent.invoke(
        agent_input,
        config={
            "callbacks": [handler],
            "metadata": {
                "example": "17_langfuse_session_traces",
                "turn": str(index),
                "langfuse_session_id": SESSION_ID,
                "langfuse_tags": ["deepagents-cookbook", "langfuse-session"],
            },
            "run_name": f"{TRACE_NAME}_turn_{index}",
        },
    )
    answer = result["messages"][-1].content
    langfuse_trace_id = handler.last_trace_id or ""
    trace_id = str(UUID(hex=langfuse_trace_id)) if langfuse_trace_id else ""

    return TurnResult(
        index=index,
        message=message,
        answer=answer,
        trace_id=trace_id,
        langfuse_trace_id=langfuse_trace_id,
    )


def main() -> None:
    langfuse = build_langfuse()
    agent = build_agent()
    messages = [
        "查一下订单 A1002 的状态，并用一句话回复。",
        "查一下订单 A1003 的状态，并用一句话回复。",
        "查一下订单 A1001 的状态，并用一句话回复。",
    ]

    print(f"sessionId: {SESSION_ID}")

    turns: list[TurnResult] = []
    for index, message in enumerate(messages, start=1):
        turn = run_turn(agent, index, message)
        turns.append(turn)
        print(f"\nturn {turn.index}")
        print(f"user: {turn.message}")
        print(f"traceId: {turn.trace_id}")
        print(f"assistant: {turn.answer}")

    langfuse.flush()


if __name__ == "__main__":
    main()
