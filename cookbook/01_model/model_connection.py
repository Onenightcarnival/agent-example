"""Connect a chat model to an agent implemented with DeepAgents."""

from __future__ import annotations

import os

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
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


def main() -> None:
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
        http_client=httpx.Client(trust_env=False),
        extra_body={"thinking": {"type": "disabled"}},
    )

    agent = create_deep_agent(
        model=model,
        system_prompt="你是一个中文技术写作助手。回答要短，先给结论。",
        middleware=[DisableBuiltinTools()],
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "用两句话解释 model 在 agent 里负责什么。",
                }
            ]
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
