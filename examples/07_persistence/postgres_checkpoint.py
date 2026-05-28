"""Store DeepAgents checkpoints in PostgreSQL."""

from __future__ import annotations

import os
from textwrap import dedent
from urllib.parse import quote

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver

THREAD_ID = "persistence-demo-thread"
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
        extra_body={
            "thinking": {"type": "disabled"},  # DeepSeek：关闭 thinking。
            "chat_template_kwargs": {"enable_thinking": False},  # 自部署模型服务：关闭 chat template thinking。
        },
    )


def postgres_url() -> str:
    user = quote(os.environ["POSTGRES_USER"], safe="")
    password = quote(os.environ["POSTGRES_PASSWORD"], safe="")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    database = quote(os.environ["POSTGRES_DB"], safe="")
    sslmode = os.environ.get("POSTGRES_SSLMODE", "disable")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"


def build_agent(checkpointer: PostgresSaver):
    return create_deep_agent(
        model=build_model(),
        system_prompt=dedent(
            """
            你是中文技术文档助手。
            这个示例只演示 checkpoint 恢复。
            不调用工具，不写 XML 标签，不输出工具调用样式。
            只用普通中文回答。
            不编造依赖、表结构或未提供的实现细节。
            如果用户让你继续，就沿用当前 thread 里已经保存的主题和约束。
            """
        ).strip(),
        checkpointer=checkpointer,
        middleware=[DisableBuiltinTools()],
    )


def run_turn(agent, user_input: str) -> str:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config={"configurable": {"thread_id": THREAD_ID}},
    )
    return result["messages"][-1].content


def main() -> None:
    config = {"configurable": {"thread_id": THREAD_ID}}

    with PostgresSaver.from_conn_string(postgres_url()) as checkpointer:
        checkpointer.setup()

        first_agent = build_agent(checkpointer)
        first_answer = run_turn(
            first_agent,
            dedent(
                """
                我想写第 07 章示例。
                主题是把 DeepAgents 的 checkpoint 外置到本地 PostgreSQL。
                示例要说明进程重启后还能按 thread_id 继续。
                先用三句话确认你记住了什么。
                """
            ).strip(),
        )
        print("\n第一次运行：")
        print(first_answer)

        second_agent = build_agent(checkpointer)
        second_answer = run_turn(
            second_agent,
            "继续刚才的主题。只根据刚才保存的信息，说这个示例要验证什么，最多 3 条。",
        )
        print("\n第二次运行：")
        print(second_answer)

        checkpoints = list(checkpointer.list(config, limit=3))
        print(f"\n已写入 checkpoint 数量：{len(checkpoints)}")


if __name__ == "__main__":
    main()
