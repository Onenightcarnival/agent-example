"""Run the smallest DeepAgents example with one model."""

from __future__ import annotations

import os

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI


def main() -> None:
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
    )

    agent = create_deep_agent(
        model=model,
        system_prompt="你是一个中文技术写作助手。回答要短，先给结论。",
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "用两句话解释 agent 为什么需要 tool。",
                }
            ]
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
