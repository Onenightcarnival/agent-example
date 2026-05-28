"""Load a local skill and ask the agent to list available skills."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI


def main() -> None:
    root = Path("examples/05_skills").resolve()
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
        http_client=httpx.Client(trust_env=False),
        extra_body={
            "thinking": {"type": "disabled"},  # DeepSeek：关闭 thinking。
            "chat_template_kwargs": {"enable_thinking": False},  # 自部署模型服务：关闭 chat template thinking。
        },
    )

    agent = create_deep_agent(
        model=model,
        system_prompt="你是 skill 说明助手。回答要短，只说明当前可用 skill。",
        skills=["/skills"],
        backend=FilesystemBackend(root_dir=root, virtual_mode=True),
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "告诉我你现在有哪些技能可用。",
                }
            ],
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
