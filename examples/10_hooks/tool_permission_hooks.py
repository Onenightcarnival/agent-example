"""Control tool calls with a middleware hook."""

from __future__ import annotations

import os
from typing import Any, NotRequired, TypedDict

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
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

ROLE_TOOL_POLICY = {
    "guest": frozenset({"read_doc", "search_web"}),
    "operator": frozenset({"read_doc", "search_web", "send_email"}),
    "admin": frozenset({"read_doc", "search_web", "send_email", "delete_file"}),
}

SAFE_DELETE_PREFIX = "/tmp/demo/"


class RequestContext(TypedDict):
    user_role: str
    audit_log: NotRequired[list[str]]


def tool_name(tool) -> str | None:
    if isinstance(tool, dict):
        name = tool.get("name")
        return name if isinstance(name, str) else None
    name = getattr(tool, "name", None)
    return name if isinstance(name, str) else None


def context_value(context: Any, key: str, default: Any = None) -> Any:
    if isinstance(context, dict):
        return context.get(key, default)
    return getattr(context, key, default)


def audit(context: Any, message: str) -> None:
    audit_log = context_value(context, "audit_log")
    if isinstance(audit_log, list):
        audit_log.append(message)


def denied_tool_message(tool_call: dict[str, Any], reason: str) -> ToolMessage:
    return ToolMessage(
        content=f"权限检查拒绝：{reason}",
        name=tool_call["name"],
        tool_call_id=tool_call["id"],
        status="error",
    )


class ToolPermissionMiddleware(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        tools = [tool for tool in request.tools if tool_name(tool) not in BUILTIN_TOOLS]
        return handler(request.override(tools=tools))

    def wrap_tool_call(self, request, handler):
        context = request.runtime.context
        role = context_value(context, "user_role", "guest")
        call = request.tool_call
        name = call["name"]
        allowed_tools = ROLE_TOOL_POLICY.get(role, ROLE_TOOL_POLICY["guest"])

        if name not in allowed_tools:
            reason = f"role={role} 不允许调用 tool={name}"
            audit(context, f"deny {name}: {reason}")
            return denied_tool_message(call, reason)

        if name == "delete_file":
            path = call.get("args", {}).get("path", "")
            if not isinstance(path, str) or not path.startswith(SAFE_DELETE_PREFIX):
                reason = f"delete_file 只能处理 {SAFE_DELETE_PREFIX} 下的路径"
                audit(context, f"deny {name}: {reason}")
                return denied_tool_message(call, reason)

        audit(context, f"allow {name}: role={role}")
        return handler(request)


def read_doc(topic: str) -> str:
    """Read an internal document by topic."""
    docs = {
        "refund": "退款文档：订单取消后，财务会在 3 个工作日内发起退款。",
        "deploy": "发布文档：上线前需要确认测试通过、迁移脚本已备份。",
    }
    return docs.get(topic, "没有找到对应文档。")


def search_web(query: str) -> str:
    """Search public information. This demo returns a fixed result."""
    return f"模拟搜索结果：{query} 暂无新的公开变更。"


def send_email(to: str, subject: str, body: str) -> str:
    """Queue an email without sending it in this demo."""
    return f"邮件已进入发送队列：to={to}, subject={subject}, body={body}"


def delete_file(path: str) -> str:
    """Delete a file path. This demo does not touch the real filesystem."""
    return f"已模拟删除：{path}"


def build_agent():
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
        http_client=httpx.Client(trust_env=False),
        extra_body={"thinking": {"type": "disabled"}},
    )

    return create_deep_agent(
        model=model,
        tools=[read_doc, search_web, send_email, delete_file],
        context_schema=RequestContext,
        system_prompt=(
            "你是内部运维助手。需要读取文档、搜索、发邮件或删除文件时，必须调用对应 tool。"
            "如果 tool 返回权限错误，直接告诉用户被拒绝的原因，不要假装已经完成。"
        ),
        middleware=[ToolPermissionMiddleware()],
    )


def run_case(agent, role: str, message: str) -> None:
    context: RequestContext = {"user_role": role, "audit_log": []}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        context=context,
    )

    print(f"\nrole: {role}")
    print(f"user: {message}")
    print(f"assistant: {result['messages'][-1].content}")
    print("audit:")
    for entry in context["audit_log"]:
        print(f"- {entry}")


def main() -> None:
    agent = build_agent()
    run_case(agent, "guest", "读取 refund 文档，并用一句话说明退款时间。")
    run_case(agent, "guest", "删除 /tmp/demo/old-report.csv。")
    run_case(agent, "admin", "删除 /tmp/demo/old-report.csv。")


if __name__ == "__main__":
    main()
