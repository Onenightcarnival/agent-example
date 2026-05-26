"""Show how Python tools and MCP tools work together in an agent."""

from __future__ import annotations

import asyncio
import os
from datetime import timedelta

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

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

    async def awrap_model_call(self, request, handler):
        tools = [tool for tool in request.tools if tool_name(tool) not in BUILTIN_TOOLS]
        return await handler(request.override(tools=tools))


def get_order_status(order_id: str) -> str:
    """Return the current status for an order id."""
    orders = {
        "A1001": "已付款，等待发货",
        "A1002": "已发货，预计明天送达",
        "A1003": "已取消，退款处理中",
    }
    return orders.get(order_id, "没有找到这个订单")


def mcp_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=headers, timeout=timeout, auth=auth, trust_env=False)


async def load_sandbox_tools():
    client = MultiServerMCPClient(
        {
            "sandbox": {
                "transport": "streamable_http",
                "url": os.environ.get("SANDBOX_MCP_SERVER_URL", "http://localhost:8080/mcp"),
                "timeout": timedelta(seconds=30),
                "sse_read_timeout": timedelta(seconds=300),
                "httpx_client_factory": mcp_http_client,
            }
        }
    )
    return await client.get_tools()


async def main() -> None:
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
        http_client=httpx.Client(trust_env=False),
        extra_body={"thinking": {"type": "disabled"}},
    )
    mcp_tools = await load_sandbox_tools()

    agent = create_deep_agent(
        model=model,
        tools=[get_order_status, *mcp_tools],
        system_prompt="你是工具说明助手。",
        middleware=[DisableBuiltinTools()],
    )

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "告诉我你现在有哪些工具可用。",
                }
            ]
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
