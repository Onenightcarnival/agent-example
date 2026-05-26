"""Show how a local Python function becomes a DeepAgents tool."""

from __future__ import annotations

import os

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI


def get_order_status(order_id: str) -> str:
    """Return the current status for an order id."""
    orders = {
        "A1001": "已付款，等待发货",
        "A1002": "已发货，预计明天送达",
        "A1003": "已取消，退款处理中",
    }
    return orders.get(order_id, "没有找到这个订单")


def main() -> None:
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
    )

    agent = create_deep_agent(
        model=model,
        tools=[get_order_status],
        system_prompt="你是订单助手。需要订单状态时，先调用 tool，不要猜。",
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "帮我查一下订单 A1002，现在是什么状态？",
                }
            ]
        }
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
