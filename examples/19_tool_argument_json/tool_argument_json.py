"""Return a visible tool error when tool arguments are not valid JSON."""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage


@dataclass
class DemoToolRequest:
    tool_call: dict[str, Any]

    def override(self, *, tool_call: dict[str, Any]):
        return DemoToolRequest(tool_call=tool_call)


def parse_tool_arguments(tool_call: dict[str, Any]) -> dict[str, Any] | ToolMessage:
    raw_arguments = tool_call.get("arguments")
    if raw_arguments is None:
        args = tool_call.get("args", {})
        return args if isinstance(args, dict) else {}

    if isinstance(raw_arguments, dict):
        return raw_arguments

    if not isinstance(raw_arguments, str):
        return invalid_arguments_message(tool_call, "arguments 必须是 JSON 字符串或对象。")

    try:
        args = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        return invalid_arguments_message(
            tool_call,
            f"arguments 不是合法 JSON：{exc.msg}。",
        )

    if not isinstance(args, dict):
        return invalid_arguments_message(tool_call, "arguments 必须解析成 JSON object。")

    # 真实项目可以在这里做有限修复，例如字段别名、字符串数字转整数、去掉首尾空格。
    # 修复要可解释、可记录，不要在这里猜用户意图。
    return args


def invalid_arguments_message(tool_call: dict[str, Any], reason: str) -> ToolMessage:
    name = str(tool_call.get("name", "unknown_tool"))
    call_id = str(tool_call.get("id", "unknown-call-id"))
    return ToolMessage(
        content=textwrap.dedent(f"""
            工具调用失败：tool arguments 不是可执行的参数。
            原因：{reason}
            请重新调用该 tool，并传入合法 JSON object。
        """).strip(),
        name=name,
        tool_call_id=call_id,
        status="error",
    )


class ToolArgumentJsonMiddleware(AgentMiddleware):
    def wrap_tool_call(self, request, handler):
        parsed = parse_tool_arguments(request.tool_call)
        if isinstance(parsed, ToolMessage):
            return parsed

        tool_call = {
            **request.tool_call,
            "args": parsed,
        }
        return handler(request.override(tool_call=tool_call))


def get_order_status(order_id: str) -> str:
    """Return order status by id."""
    orders = {
        "A1001": "已付款，等待发货",
        "A1002": "已发货，预计明天送达",
    }
    return orders.get(order_id.strip().upper(), "没有找到这个订单。")


def call_order_tool(request: DemoToolRequest) -> ToolMessage:
    args = request.tool_call["args"]
    result = get_order_status(args["order_id"])
    return ToolMessage(
        content=result,
        name=request.tool_call["name"],
        tool_call_id=request.tool_call["id"],
        status="success",
    )


def run_case(title: str, tool_call: dict[str, Any]) -> None:
    middleware = ToolArgumentJsonMiddleware()
    request = DemoToolRequest(tool_call=tool_call)
    result = middleware.wrap_tool_call(request, call_order_tool)

    print(f"\n{title}")
    print(f"status: {result.status}")
    print(result.content)


def main() -> None:
    valid_call = {
        "id": "call-valid",
        "name": "get_order_status",
        "arguments": '{"order_id": "A1002"}',
    }
    invalid_call = {
        "id": "call-invalid",
        "name": "get_order_status",
        "arguments": 'A1002"}',
    }

    run_case("合法 arguments", valid_call)
    run_case("非法 arguments", invalid_call)


if __name__ == "__main__":
    main()
