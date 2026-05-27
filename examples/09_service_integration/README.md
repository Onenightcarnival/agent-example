# 09 service integration

## 场景

agent 最终通常要被应用系统调用，而不是只在命令行里运行。

这个示例把订单 agent 包成 FastAPI 服务。调用方从 HTTP header 传入 `session_id`、`trace_id` 和 `thread_id`。服务把这些身份信息继续传给 DeepAgents 和 Langfuse。

示例提供两个接口：

- `POST /chat`：同步返回 agent 的最终回答。
- `POST /chat/stream`：把 DeepAgents 的内部 stream 事件转换成服务自己的 SSE 协议。

这里的重点不是 FastAPI 本身，而是服务边界。接口输入、运行身份、trace 和流式事件都由服务层定义，调用方不直接依赖 DeepAgents 的内部数据结构。

## 代码

见 [service_app.py](service_app.py)。

## 运行方式

先确认 `.env` 里有模型变量和 Langfuse 变量：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash

LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxx
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

如果使用 Langfuse US 区域，`LANGFUSE_BASE_URL` 改成：

```bash
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

启动服务：

```bash
uv run --env-file .env uvicorn examples.09_service_integration.service_app:app --reload
```

调用同步接口：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'content-type: application/json' \
  -H 'x-session-id: order-session-001' \
  -H 'x-trace-id: 5f4d9f02-6d2b-4a2d-9c0a-8f6e7b9a1c23' \
  -H 'x-thread-id: order-thread-001' \
  -d '{"message":"查一下订单 A1002 的状态，并用一句话回复。"}'
```

调用 SSE 接口：

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H 'content-type: application/json' \
  -H 'x-session-id: order-session-001' \
  -H 'x-trace-id: 3a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71' \
  -H 'x-thread-id: order-thread-001' \
  -d '{"message":"继续刚才的会话，再查一下订单 A1003。"}'
```

SSE 返回的是服务协议，不是 DeepAgents 的原始事件：

```text
event: request.started
data: {"session_id":"order-session-001","trace_id":"3a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71","thread_id":"order-thread-001"}

event: message.delta
data: {"session_id":"order-session-001","trace_id":"3a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71","thread_id":"order-thread-001","delta":"订单"}

event: tool.start
data: {"session_id":"order-session-001","trace_id":"3a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71","thread_id":"order-thread-001","tool_name":"get_order_status"}

event: tool.end
data: {"session_id":"order-session-001","trace_id":"3a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71","thread_id":"order-thread-001","tool_name":"get_order_status"}

event: message.done
data: {"session_id":"order-session-001","trace_id":"3a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71","thread_id":"order-thread-001","answer":"订单 A1003 已取消，退款处理中。"}
```

## 关键点

- `ChatRequest` 和 `ChatResponse` 是服务 API 的边界。调用方只看到 `message`、`metadata` 和最终回答，不直接看到 agent 的内部 `state`。
- `x-session-id` 表示业务会话。示例允许缺省，缺省时服务生成一个新的 `session_id`。
- `x-trace-id` 表示观测 trace。示例按 UUID 接收它。Langfuse `TraceContext` 要求 32 位小写 hex，所以代码会把 UUID 转成 `.hex` 后传给 Langfuse。响应和 SSE event 仍然返回原来的 UUID 字符串。
- `x-thread-id` 表示 DeepAgents / LangGraph 的运行现场。服务把它放进 `configurable.thread_id`。
- 服务先创建 Langfuse 根 span，再用 `propagate_attributes(session_id=...)` 传播 session。这样 LangChain callback 产生的 observations 会进入 Sessions 看板。
- 业务 `metadata` 写在服务根 span 上。`tags` 会通过 `propagate_attributes(...)` 传播。不要把密钥、完整隐私信息或敏感业务数据放进去。
- `/chat/stream` 使用 `astream_events` 读取内部事件，再转换成 `request.started`、`message.delta`、`tool.start`、`tool.end`、`message.done` 和 `error`。
- 前端不应该直接依赖 DeepAgents 的内部 stream 事件。服务协议稳定后，后端可以调整 agent 框架、tool 名或运行细节。

## 取舍

这个示例只演示同步 HTTP 和 SSE 两种入口。它没有加入鉴权、限流、队列、任务表、重试和告警。

如果 agent 运行时间很长，可以改成异步任务：接口先返回任务 id，后台执行 agent，再让调用方轮询状态或订阅任务事件。无论使用哪种形态，`session_id`、`trace_id` 和 `thread_id` 都应该在服务边界处明确下来。
