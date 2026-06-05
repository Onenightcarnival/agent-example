# 19 tool argument json

## 场景

模型已经输出了 tool call，运行时也识别出了 tool 名和调用 ID。

但 `arguments` 字段不是合法 JSON。比如模型输出了 `A1002"}`，而不是 `{"order_id": "A1002"}`。这时 tool 还没有拿到可用的 `args`，直接执行会失败。

这个示例演示一种保守做法：在 tool 调用前解析 `arguments`。如果解析失败，不执行原 tool，而是返回一条 `status="error"` 的 `ToolMessage`。模型会看到失败原因，下一轮可以重新调用 tool。

## 代码

见 [tool_argument_json.py](tool_argument_json.py)。

## 运行方式

```bash
uv run python examples/19_tool_argument_json/tool_argument_json.py
```

输出里会有两次调用：

- 合法 `arguments` 会转成 `args`，再执行 `get_order_status`。
- 非法 `arguments` 会短路，返回一条 tool 失败结果。

示例输出：

```text
合法 arguments
status: success
已发货，预计明天送达

非法 arguments
status: error
工具调用失败：tool arguments 不是可执行的参数。
原因：arguments 不是合法 JSON：Expecting value。
请重新调用该 tool，并传入合法 JSON object。
```

## 关键点

- 这个问题发生在 tool 执行前。tool call 已经被识别，但 `arguments` 还不能反序列化成 `dict`。
- `ToolArgumentJsonMiddleware.wrap_tool_call(...)` 先解析 `request.tool_call["arguments"]`。
- 解析成功时，把结果写回 `tool_call["args"]`，再调用 `handler(request)`。
- 解析失败时，直接返回 `ToolMessage(status="error")`，不执行原 tool。
- 返回的错误要给模型看得懂。它应该说明哪个字段错了，以及下一次应该传合法 JSON object。

## 取舍

这个示例不修复模型输出，只把失败原因塞回 tool 结果。这样 trace 里能看到模型原始输出，也能看到为什么没有执行 tool。

真实项目可以做有限的入参修复，比如字段别名、字符串数字转整数、去掉首尾空格。修复要有边界，也要能记录。不要在 wrapper 里猜用户意图；需要重新理解用户问题时，让模型再调用一次 tool。

如果运行时在进入 `wrap_tool_call` 前就已经丢掉了非法 `arguments`，就需要把这段逻辑放到更靠前的 tool dispatch wrapper 里。原则不变：失败要变成模型可见的 tool 结果，而不是静默吞掉。
