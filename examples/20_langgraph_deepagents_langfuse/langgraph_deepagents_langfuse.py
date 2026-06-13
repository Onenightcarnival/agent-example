"""Run DeepAgents as one LangGraph node and trace it with Langfuse."""

from __future__ import annotations

import os
from typing import Any, TypedDict
from uuid import UUID, uuid4

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START, StateGraph

BUILTIN_TOOLS = frozenset(
    {
        "write_todos",
        "ls",
        "read_file",
        "write_file",
        "edit_file",
        "glob",
        "grep",
        "execute",
        "task",
    }
)


class GraphState(TypedDict, total=False):
    session_id: str
    question: str
    route: str
    answer: str
    needs_review: bool


def tool_name(tool: Any) -> str | None:
    if isinstance(tool, dict):
        name = tool.get("name")
        return name if isinstance(name, str) else None
    name = getattr(tool, "name", None)
    return name if isinstance(name, str) else None


class DisableBuiltinTools(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        tools = [tool for tool in request.tools if tool_name(tool) not in BUILTIN_TOOLS]
        return handler(request.override(tools=tools))


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


def get_order_status(order_id: str) -> str:
    """Return the current status for an order id."""
    orders = {
        "A1001": "已付款，等待发货",
        "A1002": "已发货，预计明天送达",
        "A1003": "已取消，退款处理中",
    }
    return orders.get(order_id.strip().upper(), "没有找到这个订单。")


def build_agent():
    return create_deep_agent(
        model=build_model(),
        tools=[get_order_status],
        system_prompt="你是订单助手。回答要短。如果需要订单状态，就调用工具查询。",
        middleware=[DisableBuiltinTools()],
    )


def classify_request(state: GraphState) -> GraphState:
    route = "order" if "订单" in state["question"] else "general"
    return {"route": route}


def build_graph():
    order_agent = build_agent()

    def call_deepagents(state: GraphState, config: RunnableConfig) -> GraphState:
        result = order_agent.invoke(
            {"messages": [{"role": "user", "content": state["question"]}]},
            config=config,
        )
        return {"answer": result["messages"][-1].content}

    def decide_next_action(state: GraphState) -> GraphState:
        answer = state["answer"]
        needs_review = "没有找到" in answer or "退款" in answer
        return {"needs_review": needs_review}

    builder = StateGraph(GraphState)
    builder.add_node("classify_request", classify_request)
    builder.add_node("deepagents_order_node", call_deepagents)
    builder.add_node("decide_next_action", decide_next_action)
    builder.add_edge(START, "classify_request")
    builder.add_edge("classify_request", "deepagents_order_node")
    builder.add_edge("deepagents_order_node", "decide_next_action")
    builder.add_edge("decide_next_action", END)
    return builder.compile()


def build_langfuse() -> Langfuse:
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        base_url=os.environ["LANGFUSE_BASE_URL"],
    )


def build_config(session_id: str, handler: CallbackHandler) -> RunnableConfig:
    return {
        "callbacks": [handler],
        "configurable": {
            "thread_id": f"thread-{session_id}",
        },
        "metadata": {
            "example": "20_langgraph_deepagents_langfuse",
            "langfuse_session_id": session_id,
            "langfuse_tags": ["deepagents-cookbook", "langgraph-deepagents"],
        },
        "run_name": "langgraph_deepagents_langfuse_demo",
    }


def main() -> None:
    session_id = str(uuid4())
    langfuse = build_langfuse()
    handler = CallbackHandler(public_key=os.environ["LANGFUSE_PUBLIC_KEY"])
    graph = build_graph()

    result = graph.invoke(
        {
            "session_id": session_id,
            "question": "查一下订单 A1003 的状态。如果需要人工处理，也告诉我。",
        },
        config=build_config(session_id, handler),
    )

    langfuse_trace_id = handler.last_trace_id or ""
    trace_id = str(UUID(hex=langfuse_trace_id)) if langfuse_trace_id else ""

    print(f"sessionId: {session_id}")
    print(f"threadId: thread-{session_id}")
    print(f"traceId: {trace_id}")
    print(f"answer: {result['answer']}")
    print(f"needsReview: {result['needs_review']}")

    langfuse.flush()


if __name__ == "__main__":
    main()
