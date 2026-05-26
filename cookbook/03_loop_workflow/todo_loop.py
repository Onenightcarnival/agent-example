"""Let the agent use a tool result inside its loop."""

from __future__ import annotations

import os

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI


def title_length_check(title: str) -> str:
    """Check whether a todo title is short enough for a daily task list."""
    if len(title) <= 18:
        return "标题长度合适"
    return "标题太长，请压缩到 18 个中文字符以内"


def main() -> None:
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
    )

    agent = create_deep_agent(
        model=model,
        tools=[title_length_check],
        system_prompt=(
            "你是任务整理助手。先给一个短标题，再用 title_length_check 检查。"
            "如果 tool 说太长，就改短。最后只输出标题和一句说明。"
        ),
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "把“整理 DeepAgents Cookbook 的六个主题并补齐每个主题的示例说明”改成一个今日待办。",
                }
            ]
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
