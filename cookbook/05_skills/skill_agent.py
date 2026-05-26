"""Load a local skill and ask the agent to use it."""

from __future__ import annotations

import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI


def main() -> None:
    root = Path("cookbook/05_skills").resolve()
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
    )

    agent = create_deep_agent(
        model=model,
        system_prompt="你是 cookbook 审稿助手。审稿时优先使用已有 skill。",
        skills=["/skills"],
        backend=FilesystemBackend(root_dir=root, virtual_mode=True),
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "请按 recipe_reviewer skill 审一下这段说明：通过本示例可以帮助开发者更好地理解 sandbox 能力。"
                    ),
                }
            ],
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
