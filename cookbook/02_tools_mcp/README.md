# 02 tools_mcp

## 场景

agent 只靠模型只能生成文本。它要查数据、算结果或调用系统，就需要 tool。

这个示例写一个很小的 Python tool，让 agent 查询订单状态。MCP tool 的位置相同：先把外部能力包装成 tool，再交给 `create_deep_agent`。

## 代码

见 [order_status_agent.py](order_status_agent.py)。

## 运行方式

```bash
uv run --env-file .env python cookbook/02_tools_mcp/order_status_agent.py
```

## 关键点

- 普通 Python 函数可以作为 tool 传入。
- 函数名、类型标注和 docstring 会影响模型选择 tool 的方式。
- MCP server 暴露出来的 tool，也可以放进 `tools` 列表。这个 recipe 先用本地函数讲清楚位置。

## 取舍

本地函数适合小示例和业务胶水代码。MCP 更适合复用已有系统，比如数据库、浏览器、GitHub 或内部服务。
