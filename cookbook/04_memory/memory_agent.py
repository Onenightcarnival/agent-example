"""Load long-term memory from an AGENTS.md file."""

from __future__ import annotations

import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI


def main() -> None:
    root = Path("cookbook/04_memory").resolve()
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
    )

    agent = create_deep_agent(
        model=model,
        system_prompt="你是 cookbook 维护助手。先判断读者场景，再给修改建议。",
        memory=["/memory/AGENTS.md"],
        backend=FilesystemBackend(root_dir=root, virtual_mode=True),
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "帮我写一句 recipe 开头，主题是 sandbox 权限。",
                }
            ],
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
