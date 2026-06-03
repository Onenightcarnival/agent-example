# 17 langfuse_session_traces

## 场景

一个业务会话里常常有多轮对话。比如用户先查订单 `A1002`，再查 `A1003`，最后让 agent 汇总刚才的结果。

观测上要分清三件事：

- `session_id`：业务会话。多轮对话共用一个值，用来在 Langfuse Sessions 看板聚合。
- `trace_id`：单次运行。每一轮对话都新建一个 trace，便于单独看模型调用和 tool 调用。
- `thread_id`：DeepAgents / LangGraph 的运行现场。多轮对话共用一个值，agent 才能接上前文。

这个示例跑三轮对话。脚本启动时生成一个 UUID 作为 `session_id`，再生成一个 UUID 作为 `thread_id`。三轮共用这两个值，但每一轮都有独立的 UUID `trace_id`。

运行结束后，脚本会调用 Langfuse Public API：

- 用 `trace.list(session_id=...)` 查询这个 session 下的 traces。
- 用 `observations.get_many(trace_id=...)` 查询每个 trace 的 observations。
- 打印 API 响应里读到的 `sessionId`。Python SDK 字段名是 `session_id`，对应 Public API JSON 里的 `sessionId`。

注意：`observations.get_many(...)` 使用 Langfuse v2 observations API。当前一些自部署版本会返回 “v2 APIs are currently in beta and only available on Langfuse Cloud”。脚本会打印这个错误。trace 查询和 Sessions 看板仍然可以验证 `sessionId` 聚合。

## 代码

见 [langfuse_session_traces.py](langfuse_session_traces.py) 和 [local_langfuse_api.py](local_langfuse_api.py)。

核心逻辑在 `run_turn(...)`：

```python
trace_uuid = uuid4()
trace_id = str(trace_uuid)
langfuse_trace_id = trace_uuid.hex
handler = CallbackHandler(trace_context=TraceContext(trace_id=langfuse_trace_id))

with langfuse.start_as_current_observation(
    as_type="span",
    name=f"{TRACE_NAME}_turn_{index}",
    trace_context=TraceContext(trace_id=langfuse_trace_id),
    input=agent_input,
    metadata={"session_id": SESSION_ID, "thread_id": THREAD_ID, "turn": str(index)},
):
    with propagate_attributes(session_id=SESSION_ID, trace_name=TRACE_NAME):
        result = agent.invoke(
            agent_input,
            config={
                "callbacks": [handler],
                "configurable": {"thread_id": THREAD_ID},
                "run_name": f"{TRACE_NAME}_turn_{index}",
            },
        )
```

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

运行示例：

```bash
uv run --env-file .env python examples/17_langfuse_session_traces/langfuse_session_traces.py
```

如果想看本地 Langfuse Public API 的原始 JSON，运行：

```bash
uv run --env-file .env python examples/17_langfuse_session_traces/local_langfuse_api.py
```

这个脚本会先跑同一组三轮对话，再请求本地 Langfuse：

```text
GET /api/public/traces?page=1&limit=100&fromTimestamp=...&toTimestamp=...
GET /api/public/v2/observations?traceId=...
```

脚本不会在 traces list 请求里传 `sessionId`。它先按本次运行的时间范围查询 traces，再在返回数据里筛出本次三条 trace，并打印每条 trace 的 `sessionId`。

如果 `.env` 里的 `LANGFUSE_BASE_URL` 不是本地地址，可以单独设置：

```bash
LANGFUSE_LOCAL_BASE_URL=http://localhost:3000
```

示例会先打印本次运行的 `sessionId` 和 `threadId`，再打印三轮对话和每轮的 `traceId`：

```text
sessionId: 3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6
threadId: 47a53cb6-0b79-4d60-9d21-9348a9061c52

turn 1
user: 查一下订单 A1002 的状态，并用一句话回复。
traceId: 8a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71
assistant: 订单 A1002 已发货，预计明天送达。

turn 2
user: 继续刚才的会话，再查一下订单 A1003。
traceId: 9b2c0b7a-4d2f-4bb1-a28a-5d61c827ab31
assistant: 订单 A1003 已取消，退款处理中。
```

随后脚本会打印 Public API 查询结果：

```text
Langfuse Public API trace sessionId:
- turn 1: traceId=8a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71, sessionId=3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6
- turn 2: traceId=9b2c0b7a-4d2f-4bb1-a28a-5d61c827ab31, sessionId=3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6
- turn 3: traceId=1c4d1321-3a02-4c69-b91b-a660447cf0bc, sessionId=3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6

Langfuse Public API observation sessionId:
- turn 1: ['3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6']
- turn 2: ['3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6']
- turn 3: ['3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6']
```

如果当前 Langfuse 部署不支持 v2 observations API，会看到：

```text
Langfuse Public API observation sessionId:
- turn 1: 当前 Langfuse 部署不支持 v2 observations API，无法读取 sessionId
  error: v2 APIs are currently in beta and only available on Langfuse Cloud
```

打开 Langfuse 项目后，也可以在 Sessions 里查看脚本打印出的 `sessionId`。里面应该能看到三条 trace。

## 关键点

- `propagate_attributes(session_id=...)` 负责把 session 写到 Langfuse trace 和 observations 上。只把 `session_id` 放进 metadata，不会进入 Sessions 聚合。
- `TraceContext(trace_id=...)` 让每轮对话使用显式 trace id。Langfuse trace id 使用 32 位 hex。示例对外打印 UUID 字符串，传给 Langfuse 时使用同一个 UUID 的 `.hex`。
- `configurable.thread_id` 用同一个 `THREAD_ID`。DeepAgents 依赖 checkpointer 续上下文，第三轮才能引用前两轮提到的订单。
- `trace_id` 和 `thread_id` 不要混用。前者给观测系统定位一次运行，后者给 agent 恢复运行现场。
- Public API 有短暂写入延迟。脚本会在 `flush()` 后轮询一会儿，再打印查询结果。
- 示例查询 observations 时使用 `fields="basic"`。这样响应会包含 `sessionId` 等基础字段，避免取回完整输入输出。
- 如果 Langfuse 部署不支持 v2 observations API，legacy observations 响应里没有 `sessionId` 字段。示例不会从 trace 结果反推这个值。

## 取舍

这个示例启动时生成 `SESSION_ID` 和 `THREAD_ID`。生产环境应该从服务边界读取它们，比如 HTTP header、用户会话表或任务表。

示例只验证 session 聚合和 Public API 字段，没有处理鉴权、脱敏、采样和长期归档。真实系统里，`session_id` 可以记录业务会话，但不要把密钥、完整手机号、身份证号或敏感订单明细放进去。
