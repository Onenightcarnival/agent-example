# 18 agent error handling

## 场景

agent 接入 FastAPI 后，错误不能直接返回给用户。

一次 `invoke` 或 `stream` 里可能有多轮模型调用，也可能调用多个 tool。这个示例只保留一个订单 tool，演示如何用 middleware 捕获运行期异常，再交给 FastAPI 统一返回。

## 代码

见 [service_app.py](service_app.py)。

## 运行方式

先确认 `.env` 里有模型变量：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash
```

启动服务：

```bash
uv run --env-file .env uvicorn examples.18_agent_error_handling.service_app:app --reload
```

调用 `invoke`：

```bash
curl -X POST http://127.0.0.1:8000/chat/invoke \
  -H 'content-type: application/json' \
  -H 'x-request-id: req-demo-001' \
  -H 'x-thread-id: thread-demo-001' \
  -d '{"message":"查一下订单 A1002 的状态。"}'
```

调用 `stream`：

```bash
curl -X POST http://127.0.0.1:8000/chat/stream \
  -H 'content-type: application/json' \
  -H 'x-request-id: req-demo-002' \
  -H 'x-thread-id: thread-demo-002' \
  -d '{"message":"查一下订单 A9999 的状态。"}'
```

如果订单 tool 报错，FastAPI 返回统一错误：

```json
{
  "code": "order_service_unavailable",
  "message": "订单服务暂时不可用，请稍后再查。",
  "request_id": "req-demo-002",
  "thread_id": "thread-demo-002",
  "source": "tool",
  "tool_name": "get_order_status",
  "retryable": true
}
```

## 关键点

- `AgentRuntimeErrorMiddleware` 是 agent 运行期的错误边界。
- `wrap_model_call` / `awrap_model_call` 捕获模型调用异常。
- `wrap_tool_call` / `awrap_tool_call` 捕获 tool 调用异常。
- `ToolBusinessError` 是 tool 主动抛出的业务错误。它保存错误码、用户提示、tool 名和是否可重试。
- `translate_error(...)` 把模型错误、tool 错误和超时错误转成 `AgentServiceError`。
- FastAPI 的 `@app.exception_handler(AgentServiceError)` 只负责把业务异常转成 JSON。
- 调用 agent 时把 `request_id` 和 `thread_id` 放进 `context`。middleware 可以从 `request.runtime.context` 里取到它们。

## 取舍

这个示例只演示 middleware 的最小做法，所以没有加入日志、重试、trace 和 MCP tool。

如果使用 MCP tool，可以在 `langchain-mcp-adapters` 的 `tool_interceptors` 里先记录 MCP server 名和 tool 名，再抛出类似 `ToolBusinessError` 的业务异常。这样 middleware 接到异常时，上下文不会丢。
