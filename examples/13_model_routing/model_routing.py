"""Route model calls between a simple model and a complex model."""

from __future__ import annotations

import os
import time
from textwrap import dedent
from typing import Any, Literal, NotRequired, TypedDict

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.output_parsers import PydanticOutputParser
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

DEFAULT_SIMPLE_MODEL_NAME = "deepseek-v4-flash"
DEFAULT_COMPLEX_MODEL_NAME = "deepseek-v4-pro"


class RouteDecision(BaseModel):
    route: Literal["simple", "complex"] = Field(description="选择 simple 或 complex")
    reason: str = Field(description="一句话说明选择原因")


class RouteContext(TypedDict):
    model_route: NotRequired[Literal["simple", "complex"]]
    route_reason: NotRequired[str]
    router_model: NotRequired[str]
    worker_model: NotRequired[str]
    route_log: NotRequired[list[str]]


def tool_name(tool: Any) -> str | None:
    if isinstance(tool, dict):
        name = tool.get("name")
        return name if isinstance(name, str) else None
    name = getattr(tool, "name", None)
    return name if isinstance(name, str) else None


def context_value(context: Any, key: str, default: Any = None) -> Any:
    if isinstance(context, dict):
        return context.get(key, default)
    return getattr(context, key, default)


def set_context_value(context: Any, key: str, value: Any) -> None:
    if isinstance(context, dict):
        context[key] = value
    else:
        setattr(context, key, value)


def latest_user_text(messages: list[Any]) -> str:
    for message in reversed(messages):
        role = getattr(message, "type", None)
        content = getattr(message, "content", None)
        if role == "human" and isinstance(content, str):
            return content
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content")
            return content if isinstance(content, str) else ""
    return ""


def model_timeout() -> float:
    return float(os.environ.get("MODEL_TIMEOUT_SECONDS", "30"))


def build_model(model_name: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
        timeout=model_timeout(),
        http_client=httpx.Client(trust_env=False),
        extra_body={
            "thinking": {"type": "disabled"},  # DeepSeek：关闭 thinking。
            "chat_template_kwargs": {"enable_thinking": False},  # 自部署模型服务：关闭 chat template thinking。
        },
    )


class SimpleComplexRouter(AgentMiddleware):
    def __init__(
        self,
        simple_model: ChatOpenAI,
        complex_model: ChatOpenAI,
        simple_model_name: str,
        complex_model_name: str,
    ) -> None:
        self.simple_model = simple_model
        self.complex_model = complex_model
        self.simple_model_name = simple_model_name
        self.complex_model_name = complex_model_name
        self.parser = PydanticOutputParser(pydantic_object=RouteDecision)

    def route_once(self, context: Any, user_text: str) -> RouteDecision:
        cached_route = context_value(context, "model_route")
        cached_reason = context_value(context, "route_reason")
        if cached_route in {"simple", "complex"} and isinstance(cached_reason, str):
            return RouteDecision(route=cached_route, reason=cached_reason)

        response = self.simple_model.invoke(
            [
                {
                    "role": "system",
                    "content": dedent(
                        f"""
                        你是模型路由器。
                        只在任务需要多步骤推理、代码方案、风险判断、长上下文整理或不确定性处理时选择 complex。
                        普通解释、改写、摘要、短问答选择 simple。

                        {self.parser.get_format_instructions()}
                        """
                    ).strip(),
                },
                {"role": "user", "content": user_text},
            ]
        )
        decision = self.parser.parse(response.content)
        set_context_value(context, "model_route", decision.route)
        set_context_value(context, "route_reason", decision.reason)

        route_log = context_value(context, "route_log")
        if isinstance(route_log, list):
            route_log.append(f"{decision.route}: {decision.reason}")

        return decision

    def wrap_model_call(self, request, handler):
        tools = [tool for tool in request.tools if tool_name(tool) not in BUILTIN_TOOLS]
        decision = self.route_once(request.runtime.context, latest_user_text(request.messages))
        model = self.complex_model if decision.route == "complex" else self.simple_model
        worker_model_name = self.complex_model_name if decision.route == "complex" else self.simple_model_name
        set_context_value(request.runtime.context, "router_model", self.simple_model_name)
        set_context_value(request.runtime.context, "worker_model", worker_model_name)
        print(f"route: {decision.route} ({decision.reason})", flush=True)
        print(f"router_model: {self.simple_model_name}", flush=True)
        print(f"worker_model: {worker_model_name}", flush=True)
        return handler(request.override(model=model, tools=tools))


def build_agent():
    simple_model_name = (
        os.environ.get("MODEL_SIMPLE_NAME")
        or os.environ.get("MODEL_FLASH_NAME")
        or os.environ.get("MODEL_NAME")
        or DEFAULT_SIMPLE_MODEL_NAME
    )
    complex_model_name = (
        os.environ.get("MODEL_COMPLEX_NAME") or os.environ.get("MODEL_PRO_NAME") or DEFAULT_COMPLEX_MODEL_NAME
    )

    simple_model = build_model(simple_model_name)
    complex_model = build_model(complex_model_name)

    return create_deep_agent(
        model=simple_model,
        context_schema=RouteContext,
        system_prompt="你是中文技术助手。回答要短，先给结论。",
        middleware=[SimpleComplexRouter(simple_model, complex_model, simple_model_name, complex_model_name)],
    )


def run_case(agent, message: str) -> None:
    context: RouteContext = {"route_log": []}
    started_at = time.perf_counter()
    print(f"\nuser: {message}", flush=True)
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            context=context,
        )
    except Exception as exc:
        elapsed = time.perf_counter() - started_at
        print(f"error: {type(exc).__name__}: {exc}")
        print(f"elapsed: {elapsed:.1f}s")
        return

    elapsed = time.perf_counter() - started_at
    print(f"assistant: {result['messages'][-1].content}")
    print(f"elapsed: {elapsed:.1f}s")


def main() -> None:
    agent = build_agent()
    run_case(agent, "我刚接触 DeepAgents，用两句话解释 model 在 agent 里负责什么。")
    run_case(
        agent,
        dedent(
            """
            我们现在所有请求都用 deepseek-v4-flash。
            请设计一个最小改造方案，让简单问答继续用 flash，复杂任务切到 pro。
            不要读取项目结构，只基于这段描述说明路由规则、接入位置和可能误判的地方。
            """
        ).strip(),
    )


if __name__ == "__main__":
    main()
