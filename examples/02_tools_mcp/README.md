# 02 tools_mcp

## 场景

agent 只靠模型只能生成文本。它要查数据、算结果或调用系统，就需要 tool。

这个示例同时接入两类 tool：

- 本地 Python 函数 `get_order_status`，用于查询订单状态。
- AIO Sandbox 暴露的 MCP tools，用于访问终端、文件和浏览器等外部能力。

DeepAgents 自带文件和命令工具。这个示例会在模型调用前过滤这些内置工具，只保留显式传入的 Python tool 和 MCP tool。运行后，用户只问 agent 当前有哪些工具可用。

## 代码

见 [tool_mcp_integration.py](tool_mcp_integration.py)。

## 运行方式

先启动本地 AIO Sandbox MCP 服务。示例默认连接：

```bash
http://localhost:8080/mcp
```

如果端口或路径不同，在 `.env` 里设置：

```bash
SANDBOX_MCP_SERVER_URL=http://localhost:8080/mcp
```

如果 sandbox MCP server 需要鉴权，也在 `.env` 里设置 auth：

```bash
SANDBOX_MCP_AUTH_HEADER="Authorization: Bearer xxxx"
```

代码会把这个值作为 MCP 请求的 header。

模型环境变量沿用第一章：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-pro
```

运行：

```bash
uv run --env-file .env python examples/02_tools_mcp/tool_mcp_integration.py
```

## 关键点

- 普通 Python 函数可以作为 tool 传入。
- 函数名、类型标注和 docstring 会影响模型选择 tool 的方式。
- `MultiServerMCPClient` 会从 MCP server 读取 tools。
- AIO Sandbox 使用 streamable HTTP transport，地址是 `http://localhost:8080/mcp`。
- Python tool 和 MCP tool 可以放在同一个 `tools` 列表里。
- `DisableBuiltinTools` 会过滤 DeepAgents 内置工具，避免示例调用到默认文件或命令工具。
- 这个示例只让模型列出工具，不调用工具。
- MCP server 没启动时，示例会在加载 tools 时报错。

## 取舍

本地函数适合小示例和业务胶水代码。MCP 更适合复用已有系统，比如数据库、浏览器、GitHub、内部服务或 sandbox。

本章只展示接入方式。tool 的具体调用放到后续章节展开，MCP tool 的权限、白名单和审计放到 sandbox 章节继续展开。
