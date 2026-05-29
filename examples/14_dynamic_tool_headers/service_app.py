"""Forward request-level headers to MCP tools from a service endpoint."""

from __future__ import annotations

import os
from datetime import timedelta
from functools import lru_cache
from typing import Any
from uuid import uuid4

import httpx
from deepagents import create_deep_agent
from fastapi import FastAPI, Header
from langchain.agents.middleware import AgentMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
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

USER_HEADER_NAMES = ("Authorization", "Cookie", "X-Tenant-Id")
SERVICE_AUTH_HEADER_NAME = "X-Service-Authorization"

app = FastAPI(title="DeepAgents dynamic tool headers demo")


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入")


class ChatResponse(BaseModel):
    answer: str
    thread_id: str
    forwarded_headers: list[str]


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


def mcp_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=headers, timeout=timeout, auth=auth, trust_env=False)


def user_headers(
    authorization: str | None,
    cookie: str | None,
    x_tenant_id: str | None,
) -> dict[str, str]:
    incoming_headers = {
        "Authorization": authorization,
        "Cookie": cookie,
        "X-Tenant-Id": x_tenant_id,
    }
    return {name: value for name in USER_HEADER_NAMES if (value := incoming_headers[name])}


def exchange_service_token(static_token: str) -> str:
    """Exchange a service-held static token for a short-lived token."""
    if static_token == "static-profile-secret":
        return "dynamic-profile-token"
    return f"dynamic-{static_token[-8:]}"


def service_headers() -> dict[str, str]:
    static_token = os.environ.get("PROFILE_STATIC_TOKEN")
    if not static_token:
        return {}
    dynamic_token = exchange_service_token(static_token)
    return {SERVICE_AUTH_HEADER_NAME: f"Bearer {dynamic_token}"}


async def load_profile_tools(headers: dict[str, str]):
    client = MultiServerMCPClient(
        {
            "profile": {
                "transport": "streamable_http",
                "url": os.environ.get("PROFILE_MCP_SERVER_URL", "http://127.0.0.1:8014/mcp"),
                "headers": headers,
                "timeout": timedelta(seconds=30),
                "sse_read_timeout": timedelta(seconds=300),
                "httpx_client_factory": mcp_http_client,
            }
        }
    )
    return await client.get_tools()


@lru_cache
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


def build_agent(tools):
    return create_deep_agent(
        model=build_model(),
        tools=tools,
        system_prompt="""
        你是资料助手。需要当前用户资料时，调用 get_current_user_profile。
        不要询问、猜测或输出 Authorization、Cookie、X-Service-Authorization 等 header。
        """.strip(),
        middleware=[DisableBuiltinTools()],
    )


def final_answer(result: dict[str, Any]) -> str:
    return result["messages"][-1].content


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
    cookie: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None),
    x_thread_id: str | None = Header(default=None),
) -> ChatResponse:
    headers = {**user_headers(authorization, cookie, x_tenant_id), **service_headers()}
    tools = await load_profile_tools(headers)
    agent = build_agent(tools)
    thread_id = x_thread_id or f"thread-{uuid4().hex}"

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"configurable": {"thread_id": thread_id}},
    )

    return ChatResponse(
        answer=final_answer(result),
        thread_id=thread_id,
        forwarded_headers=list(headers),
    )
