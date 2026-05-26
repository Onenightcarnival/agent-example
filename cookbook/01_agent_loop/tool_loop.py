import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def get_chapter_status(chapter: str) -> str:
    """返回 cookbook 章节状态。"""
    statuses = {
        "00": "00_model_setup 已完成，包含普通调用和 streaming 调用。",
        "01": "01_agent_loop 正在演示最小 agent loop 和工具调用 loop。",
    }
    return statuses.get(chapter, f"还没有记录 {chapter} 章的状态。")


def print_message_trace(messages: list[object]) -> None:
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, ToolMessage):
            role = f"tool:{message.name}"
        else:
            role = type(message).__name__

        content = message.content if hasattr(message, "content") else str(message)
        if content:
            print(f"[{role}] {content}")


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
        tools=[get_chapter_status],
        system_prompt=("你是一个简洁的中文项目助手。需要查询章节状态时调用工具。回答不使用 emoji。"),
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请查看 01 章状态，再用一句话回答。",
                }
            ]
        }
    )

    print_message_trace(result["messages"])


if __name__ == "__main__":
    main()
