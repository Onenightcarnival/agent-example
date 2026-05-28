"""Load long-term memory from an AGENTS.md file."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import httpx
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI


def main() -> None:
    root = Path("examples/04_memory").resolve()
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
        system_prompt=textwrap.dedent(
            """
            你是招聘顾问，负责帮客户写 JD 初稿。
            先判断业务场景，再写岗位职责、任职要求和加分项。
            """
        ).strip(),
        memory=["/memory/AGENTS.md"],
        backend=FilesystemBackend(root_dir=root, virtual_mode=True),
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": textwrap.dedent(
                        """
                        客户是一家做供应链系统的 B2B SaaS 公司，要招一名 AI 产品经理。
                        帮我写 JD 初稿。
                        """
                    ).strip(),
                }
            ],
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
