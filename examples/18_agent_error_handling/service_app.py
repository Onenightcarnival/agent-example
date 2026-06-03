"""Handle DeepAgents runtime errors with middleware."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any
from uuid import uuid4

import httpx
from deepagents import create_deep_agent
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from langchain.agents.middleware import AgentMiddleware
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APITimeoutError, RateLimitError
from pydantic import BaseModel, Field

app = FastAPI(title="DeepAgents middleware error handling demo")


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入")


class ChatResponse(BaseModel):
    answer: str
    request_id: str
    thread_id: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str
    thread_id: str
    source: str
    tool_name: str | None = None
    retryable: bool = False


class ToolBusinessError(Exception):
    def __init__(self, *, code: str, message: str, tool_name: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.tool_name = tool_name
        self.retryable = retryable


class AgentServiceError(Exception):
    status_code = 500
    code = "agent_failed"
    message = "助手暂时无法处理，请稍后再试。"
    source = "agent"
    retryable = False

    def __init__(
        self,
        *,
        request_id: str,
        thread_id: str,
        code: str | None = None,
        message: str | None = None,
        source: str | None = None,
        tool_name: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message or self.message)
        self.request_id = request_id
        self.thread_id = thread_id
        self.code = code or self.code
        self.message = message or self.message
        self.source = source or self.source
        self.tool_name = tool_name
        self.retryable = self.retryable if retryable is None else retryable


class AgentRuntimeErrorMiddleware(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        try:
            return handler(request)
        except Exception as exc:
            context = getattr(request.runtime, "context", {}) or {}
            request_id = context.get("request_id", "req-unknown")
            thread_id = context.get("thread_id", f"thread-{request_id}")
            raise translate_error(exc, request_id=request_id, thread_id=thread_id, source="model") from exc

    async def awrap_model_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as exc:
            context = getattr(request.runtime, "context", {}) or {}
            request_id = context.get("request_id", "req-unknown")
            thread_id = context.get("thread_id", f"thread-{request_id}")
            raise translate_error(exc, request_id=request_id, thread_id=thread_id, source="model") from exc

    def wrap_tool_call(self, request, handler):
        try:
            return handler(request)
        except Exception as exc:
            context = getattr(request.runtime, "context", {}) or {}
            request_id = context.get("request_id", "req-unknown")
            thread_id = context.get("thread_id", f"thread-{request_id}")
            tool_call = getattr(request, "tool_call", None)
            tool_name = tool_call.get("name") if isinstance(tool_call, dict) else None
            if not isinstance(tool_name, str):
                tool_name = getattr(getattr(request, "tool", None), "name", None)
            raise translate_error(
                exc,
                request_id=request_id,
                thread_id=thread_id,
                source="tool",
                tool_name=tool_name if isinstance(tool_name, str) else None,
            ) from exc

    async def awrap_tool_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as exc:
            context = getattr(request.runtime, "context", {}) or {}
            request_id = context.get("request_id", "req-unknown")
            thread_id = context.get("thread_id", f"thread-{request_id}")
            tool_call = getattr(request, "tool_call", None)
            tool_name = tool_call.get("name") if isinstance(tool_call, dict) else None
            if not isinstance(tool_name, str):
                tool_name = getattr(getattr(request, "tool", None), "name", None)
            raise translate_error(
                exc,
                request_id=request_id,
                thread_id=thread_id,
                source="tool",
                tool_name=tool_name if isinstance(tool_name, str) else None,
            ) from exc


@app.exception_handler(AgentServiceError)
async def agent_error_handler(_request: Request, exc: AgentServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.code,
            message=exc.message,
            request_id=exc.request_id,
            thread_id=exc.thread_id,
            source=exc.source,
            tool_name=exc.tool_name,
            retryable=exc.retryable,
        ).model_dump(),
    )


def translate_error(
    exc: Exception,
    *,
    request_id: str,
    thread_id: str,
    source: str,
    tool_name: str | None = None,
) -> AgentServiceError:
    if isinstance(exc, AgentServiceError):
        return exc
    if isinstance(exc, ToolBusinessError):
        return AgentServiceError(
            request_id=request_id,
            thread_id=thread_id,
            code=exc.code,
            message=exc.message,
            source="tool",
            tool_name=exc.tool_name,
            retryable=exc.retryable,
        )
    if isinstance(exc, RateLimitError):
        return AgentServiceError(
            request_id=request_id,
            thread_id=thread_id,
            code="model_rate_limited",
            message="当前请求太多，请稍后再试。",
            source="model",
            retryable=True,
        )
    if isinstance(exc, (APIConnectionError, APITimeoutError, httpx.TimeoutException)):
        return AgentServiceError(
            request_id=request_id,
            thread_id=thread_id,
            code="upstream_unavailable",
            message="上游服务暂时不可用，请稍后再试。",
            source=source,
            tool_name=tool_name,
            retryable=True,
        )
    return AgentServiceError(
        request_id=request_id,
        thread_id=thread_id,
        code="agent_runtime_error",
        message="助手运行出错，请稍后再试。",
        source=source,
        tool_name=tool_name,
    )


def get_order_status(order_id: str) -> str:
    """Return order status by id."""
    orders = {
        "A1001": "已付款，等待发货",
        "A1002": "已发货，预计明天送达",
    }
    order_id = order_id.strip().upper()
    if order_id == "A9999":
        raise ToolBusinessError(
            code="order_service_unavailable",
            message="订单服务暂时不可用，请稍后再查。",
            tool_name="get_order_status",
            retryable=True,
        )
    if order_id not in orders:
        raise ToolBusinessError(
            code="order_not_found",
            message="没有找到这个订单，请检查订单号。",
            tool_name="get_order_status",
        )
    return orders[order_id]


@lru_cache
def get_agent():
    return create_deep_agent(
        model=ChatOpenAI(
            model=os.environ["MODEL_NAME"],
            api_key=os.environ["MODEL_API_KEY"],
            base_url=os.environ.get("MODEL_BASE_URL") or None,
            http_client=httpx.Client(trust_env=False),
        ),
        tools=[get_order_status],
        system_prompt="你是订单助手。用户问订单状态时，调用 get_order_status。回答要短。",
        middleware=[AgentRuntimeErrorMiddleware()],
    )


@app.post("/chat/invoke", response_model=ChatResponse)
def chat_invoke(
    request: ChatRequest,
    x_request_id: str | None = Header(default=None),
    x_thread_id: str | None = Header(default=None),
) -> ChatResponse:
    request_id = x_request_id or f"req-{uuid4().hex}"
    thread_id = x_thread_id or f"thread-{request_id}"
    result = get_agent().invoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"configurable": {"thread_id": thread_id}, "run_name": "middleware_error_demo"},
        context={"request_id": request_id, "thread_id": thread_id},
    )
    return ChatResponse(answer=result["messages"][-1].content, request_id=request_id, thread_id=thread_id)


@app.post("/chat/stream", response_model=ChatResponse)
def chat_stream(
    request: ChatRequest,
    x_request_id: str | None = Header(default=None),
    x_thread_id: str | None = Header(default=None),
) -> ChatResponse:
    request_id = x_request_id or f"req-{uuid4().hex}"
    thread_id = x_thread_id or f"thread-{request_id}"
    last_chunk: dict[str, Any] | None = None
    for chunk in get_agent().stream(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"configurable": {"thread_id": thread_id}, "run_name": "middleware_error_demo"},
        context={"request_id": request_id, "thread_id": thread_id},
        stream_mode="values",
    ):
        last_chunk = chunk
    if last_chunk is None:
        raise AgentServiceError(request_id=request_id, thread_id=thread_id)
    return ChatResponse(answer=last_chunk["messages"][-1].content, request_id=request_id, thread_id=thread_id)
