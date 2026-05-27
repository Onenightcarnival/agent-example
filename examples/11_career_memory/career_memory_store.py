"""Store long-term memory as a career profile in PostgreSQL."""

from __future__ import annotations

import os
from typing import Any, Literal
from urllib.parse import quote

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolRuntime
from langgraph.store.base import BaseStore
from langgraph.store.postgres import PostgresStore

PERSON_ID = "customer-success-lin"

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

MemoryKind = Literal["profile", "preference", "experience", "lesson"]


def tool_name(tool_def: Any) -> str | None:
    if isinstance(tool_def, dict):
        name = tool_def.get("name")
        return name if isinstance(name, str) else None
    name = getattr(tool_def, "name", None)
    return name if isinstance(name, str) else None


class DisableBuiltinTools(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        tools = [tool_def for tool_def in request.tools if tool_name(tool_def) not in BUILTIN_TOOLS]
        return handler(request.override(tools=tools))


def postgres_url() -> str:
    user = quote(os.environ["POSTGRES_USER"], safe="")
    password = quote(os.environ["POSTGRES_PASSWORD"], safe="")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    database = quote(os.environ["POSTGRES_DB"], safe="")
    sslmode = os.environ.get("POSTGRES_SSLMODE", "disable")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"


def build_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
        http_client=httpx.Client(trust_env=False),
        extra_body={"thinking": {"type": "disabled"}},
    )


def person_namespace(kind: MemoryKind) -> tuple[str, str, str]:
    return ("person", PERSON_ID, kind)


def seed_career_memory(store: BaseStore) -> None:
    store.put(
        person_namespace("profile"),
        "role",
        {
            "kind": "profile",
            "content": "长期负责 B2B SaaS 客户成功，熟悉客户上线、权限配置、续费跟进和工单升级。",
            "source": "career_profile",
            "confidence": "high",
        },
    )
    store.put(
        person_namespace("preference"),
        "acme_contact_style",
        {
            "kind": "preference",
            "content": "Acme 的运营负责人只看结论、明确时间点和下一步，不喜欢长解释。",
            "source": "account_note",
            "confidence": "high",
        },
    )
    store.put(
        person_namespace("experience"),
        "acme_launch",
        {
            "kind": "experience",
            "content": "Acme 上线前常遇到角色权限和报表可见性问题，通常要同时确认账号角色、环境和报表 ID。",
            "source": "handover_note",
            "confidence": "high",
        },
    )
    store.put(
        person_namespace("lesson"),
        "confirm_environment",
        {
            "kind": "lesson",
            "content": "处理权限问题时，先确认客户用的是测试环境还是生产环境。上次没确认环境，排查方向错了。",
            "source": "incident_review",
            "confidence": "medium",
        },
    )


def format_items(items: list[Any]) -> str:
    if not items:
        return "没有找到相关履历记忆。"
    lines = []
    for item in items:
        value = item.value
        lines.append(
            "- "
            f"{value.get('kind')} / {item.key}: "
            f"{value.get('content')} "
            f"(source={value.get('source')}, confidence={value.get('confidence')})"
        )
    return "\n".join(lines)


@tool
def recall_career_memory(kind: MemoryKind, runtime: ToolRuntime) -> str:
    """Recall one kind of long-term career memory for the current person."""
    if runtime.store is None:
        return "当前 agent 没有配置 store。"
    items = runtime.store.search(person_namespace(kind), limit=5)
    return format_items(items)


@tool
def save_career_memory(kind: MemoryKind, key: str, content: str, source: str, runtime: ToolRuntime) -> str:
    """Save a durable career memory when it can help future tasks."""
    if runtime.store is None:
        return "当前 agent 没有配置 store。"
    runtime.store.put(
        person_namespace(kind),
        key,
        {
            "kind": kind,
            "content": content,
            "source": source,
            "confidence": "medium",
        },
    )
    return f"已写入 {kind}: {key}"


def build_agent(store: BaseStore):
    return create_deep_agent(
        model=build_model(),
        tools=[recall_career_memory, save_career_memory],
        system_prompt=(
            "你是客户成功助手，帮助客户成功经理处理客户请求和账户交接。长期记忆按职业履历理解："
            "profile 是稳定背景，preference 是偏好，experience 是做过的事，lesson 是踩坑记录。"
            "开始新任务前，先调用 recall_career_memory 读取相关履历记忆。"
            "只有能跨任务复用的信息，才调用 save_career_memory 写入长期记忆。"
            "如果信息已经在履历里，不要重复写入，只说明已存在。"
            "当前任务里的临时事实不要写入长期记忆。"
            "客户请求里的紧急问题先给可执行处理方案。"
            "涉及外部承诺时，要给清楚的时间点和下一步。"
            "不要承诺一定解决，只承诺排查节奏、反馈时间和下一步动作。"
            "不要使用保证、一定、落地这类承诺词。"
            "不要把履历里的长期经验改写成具体日期或具体历史事件。"
            "不要编造已经完成的排查结果。回答要短。"
        ),
        store=store,
        middleware=[DisableBuiltinTools()],
    )


def main() -> None:
    with PostgresStore.from_conn_string(postgres_url()) as store:
        store.setup()
        seed_career_memory(store)

        agent = build_agent(store)
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Acme 客户说管理员看不到新建报表，今天上线前必须解决。"
                            "请先参考我的职业履历记忆，再给客户成功经理一份处理建议。"
                            "输出包括：先问什么、怎么回客户、哪些信息不写入长期记忆。"
                        ),
                    }
                ]
            },
        )

        print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
