"""Trace a DeepAgents run with Langfuse."""

from __future__ import annotations

import os

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


def tool_name(tool) -> str | None:
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
        extra_body={"thinking": {"type": "disabled"}},
    )


def get_order_status(order_id: str) -> str:
    """Return the current status for an order id."""
    orders = {
        "A1001": "已付款，等待发货",
        "A1002": "已发货，预计明天送达",
        "A1003": "已取消，退款处理中",
    }
    return orders.get(order_id, "没有找到这个订单")


def main() -> None:
    langfuse = Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        base_url=os.environ["LANGFUSE_BASE_URL"],
    )
    langfuse_handler = CallbackHandler(public_key=os.environ["LANGFUSE_PUBLIC_KEY"])

    agent = create_deep_agent(
        model=build_model(),
        tools=[get_order_status],
        system_prompt="你是订单助手。回答要短。如果需要订单状态，就调用工具查询。",
        middleware=[DisableBuiltinTools()],
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "查一下订单 A1002 的状态，并用一句话回复。",
                }
            ]
        },
        config={
            "callbacks": [langfuse_handler],
            "metadata": {
                "example": "08_observability",
                "thread_id": "langfuse-demo-thread",
            },
            "run_name": "langfuse_observability_demo",
            "tags": ["deepagents-cookbook", "observability"],
        },
    )

    print(result["messages"][-1].content)
    langfuse.flush()


if __name__ == "__main__":
    main()
