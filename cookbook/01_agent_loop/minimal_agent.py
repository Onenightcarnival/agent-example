import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def main() -> None:
    load_dotenv(".env")

    model = ChatOpenAI(
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ["MODEL_BASE_URL"],
        model=os.environ["MODEL_NAME"],
        extra_body={"thinking": {"type": "disabled"}},
    )
    agent = create_deep_agent(
        model=model,
        tools=[],
        system_prompt="你是一个简洁的中文技术助手。回答不使用 emoji。",
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "用一句话说明 agent loop 做了什么。",
                }
            ]
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
