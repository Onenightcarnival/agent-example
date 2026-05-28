"""Show how messages carry context across conversation turns."""

from __future__ import annotations

import os
from textwrap import dedent

import httpx
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI


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


def main() -> None:
    agent = create_deep_agent(
        model=build_model(),
        system_prompt=dedent(
            """
            你是 Agent Example 的选题助手。
            用户想新增示例，但一开始通常说不完整。
            每个 turn 只做一件事：信息不够就追问一个问题，信息够了就整理成 example brief。
            example brief 需要包含：主题、场景、运行结果、环境变量。
            """
        ).strip(),
    )

    messages = []
    user_inputs = [
        "我想写一个关于 memory 的示例。",
        "场景是让 agent 记住用户偏好，比如用户说以后回答短一点。",
        "读者运行后，应该看到第二次回答沿用这个偏好。不需要外部服务，只用模型变量。",
    ]

    for index, user_input in enumerate(user_inputs, start=1):
        print(f"\nturn {index} user:\n{user_input}\n")

        result = agent.invoke(
            {
                "messages": [
                    *messages,
                    {"role": "user", "content": user_input},
                ]
            }
        )
        messages = result["messages"]

        print(f"turn {index} assistant:\n{messages[-1].content}\n")


if __name__ == "__main__":
    main()
