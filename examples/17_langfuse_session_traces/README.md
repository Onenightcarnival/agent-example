# 17 langfuse_session_traces

## 场景

08 号示例已经演示了无侵入式 tracing：agent、tool 和提示词不需要改，只在运行时挂一个 Langfuse callback。

这个示例只多做一件事：在 `agent.invoke(..., config=...)` 里传入 `langfuse_session_id`。这样每轮请求仍然是独立 trace，但 Langfuse 可以按同一个 session 聚合。

示例会连续跑三次订单查询：

- 每次 `agent.invoke(...)` 都是一次独立运行。
- 每次运行都会生成一条独立 trace。
- 三条 trace 共用同一个 UUID `session_id`。
- 打开 Langfuse Sessions 看板，可以按这个 `session_id` 看到三条 trace。

这里不演示 DeepAgents 的 `thread_id` 和 checkpoint。session 只负责观测聚合，不负责让 agent 记住前文。

## 代码

主示例见 [langfuse_session_traces.py](langfuse_session_traces.py)。如果想看 Langfuse Public API 的原始返回，再看 [local_langfuse_api.py](local_langfuse_api.py)。

核心逻辑和 08 号示例一样，仍然只挂 `CallbackHandler`。区别是 `metadata` 里多了 `langfuse_session_id`：

```python
handler = CallbackHandler(public_key=os.environ["LANGFUSE_PUBLIC_KEY"])

result = agent.invoke(
    agent_input,
    config={
        "callbacks": [handler],
        "metadata": {
            "example": "17_langfuse_session_traces",
            "turn": str(index),
            "langfuse_session_id": SESSION_ID,
            "langfuse_tags": ["deepagents-cookbook", "langfuse-session"],
        },
        "run_name": f"{TRACE_NAME}_turn_{index}",
    },
)
```

`langfuse_session_id` 是 Langfuse LangChain callback 识别的字段。它会写到 trace 的 `sessionId` 上。普通的 `session_id` metadata 只会变成 metadata，不会进入 Sessions 聚合。

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

示例会打印本次运行的 `sessionId`，以及每轮 trace：

```text
sessionId: 3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6

turn 1
user: 查一下订单 A1002 的状态，并用一句话回复。
traceId: 8a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71
assistant: 订单 A1002 已发货，预计明天送达。

turn 2
user: 查一下订单 A1003 的状态，并用一句话回复。
traceId: 9b2c0b7a-4d2f-4bb1-a28a-5d61c827ab31
assistant: 订单 A1003 已取消，退款处理中。
```

打开 Langfuse 项目后，也可以在 Sessions 里查看脚本打印出的 `sessionId`。里面应该能看到三条 trace。

如果想看本地 Langfuse Public API 的原始 JSON，运行：

```bash
uv run --env-file .env python examples/17_langfuse_session_traces/local_langfuse_api.py
```

这个脚本会先跑同一组三轮请求，再请求本地 Langfuse：

```text
GET /api/public/traces/{traceId}
GET /api/public/traces?page=1&limit=100&fromTimestamp=...&toTimestamp=...
GET /api/public/v2/observations?traceId=...
```

脚本不会在 traces list 请求里传 `sessionId`。它先按本次运行的时间范围查询 traces，再在返回数据里筛出本次三条 trace。返回的 trace 里可以看到 `sessionId`。

当前一些自部署 Langfuse 不支持 `/api/public/v2/observations`，会返回 “v2 APIs are currently in beta and only available on Langfuse Cloud”。trace 查询和 Sessions 看板仍然可以验证 `sessionId` 聚合。

如果 `.env` 里的 `LANGFUSE_BASE_URL` 不是本地地址，可以单独设置：

```bash
LANGFUSE_LOCAL_BASE_URL=http://localhost:3000
```

## 关键点

- 这个示例仍然是无侵入式 tracing。agent 创建逻辑、tool 逻辑和业务提示词不需要为了 session 改写。
- `CallbackHandler` 负责记录 LangChain / LangGraph 运行。DeepAgents 可以直接复用它。
- `langfuse_session_id` 放在 `config.metadata` 里。Langfuse callback 会把它写成 trace 的 `sessionId`。
- 每次 `agent.invoke(...)` 都是独立 trace。session 只做观测聚合，不等于对话记忆。
- `langfuse_tags` 也放在 `metadata` 里。它会写成 Langfuse tags。
- 短脚本退出前调用 `langfuse.flush()`，避免 trace 还没发送完进程就结束。

## 取舍

这个示例只演示最小 session 透传。它适合回答“如何在无侵入式 tracing 下，把多次请求放进同一个 Langfuse session”。

生产环境里，`session_id` 应该来自服务边界，比如 HTTP header、用户会话表或任务表。不要把密钥、完整手机号、身份证号或敏感订单明细放进去。
