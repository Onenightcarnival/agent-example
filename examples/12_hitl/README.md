# 12 HITL

## 场景

agent 可以帮客服处理工单，也可以起草邮件。但邮件一旦发出，就进入外部世界。

这个示例把邮件助手包成 FastAPI 服务。第一次请求让 agent 读取工单并准备回复。agent 调用 `send_email` 前会暂停，服务通过 SSE 返回 `review.required` 和待审核邮件。人工审核后，调用方再提交审核结果。服务用同一个 `thread_id` 恢复 agent，继续发送或取消。

这里的重点不是邮件系统，而是服务化 HITL：

- agent 负责准备动作。
- 服务把中断点变成稳定 API。
- 人工决定通过 API 回到同一个 thread。
- Langfuse 记录服务请求、agent 调用和审核结果。

## 代码

见 [hitl_email_service.py](hitl_email_service.py)。

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

启动服务：

```bash
uv run --env-file .env uvicorn examples.12_hitl.hitl_email_service:app --reload --port 8012
```

创建邮件草稿。这个接口返回 SSE：

```bash
curl -N -X POST http://127.0.0.1:8012/drafts/stream \
  -H 'content-type: application/json' \
  -H 'x-session-id: email-session-001' \
  -H 'x-trace-id: 29d6c8a3-2d86-4f1c-bba1-58d55f52f3a9' \
  -H 'x-thread-id: email-thread-001' \
  -d '{"message":"处理工单 T1001，给客户写一封简短回复。"}'
```

服务会返回待审核邮件：

```text
event: request.started
data: {"session_id":"email-session-001","trace_id":"29d6c8a3-2d86-4f1c-bba1-58d55f52f3a9","thread_id":"email-thread-001"}

event: tool.started
data: {"session_id":"email-session-001","trace_id":"29d6c8a3-2d86-4f1c-bba1-58d55f52f3a9","thread_id":"email-thread-001","tool_name":"read_ticket"}

event: tool.finished
data: {"session_id":"email-session-001","trace_id":"29d6c8a3-2d86-4f1c-bba1-58d55f52f3a9","thread_id":"email-thread-001","tool_name":"read_ticket"}

event: review.required
data: {"session_id":"email-session-001","trace_id":"29d6c8a3-2d86-4f1c-bba1-58d55f52f3a9","thread_id":"email-thread-001","review_id":"8f2f...","email":{"to":"lin@example.com","subject":"订单 A1002 物流更新说明","body":"..."}}
```

人工确认后继续发送：

```bash
curl -N -X POST http://127.0.0.1:8012/reviews/stream \
  -H 'content-type: application/json' \
  -H 'x-session-id: email-session-001' \
  -H 'x-trace-id: 29d6c8a3-2d86-4f1c-bba1-58d55f52f3a9' \
  -H 'x-thread-id: email-thread-001' \
  -d '{"type":"approve","review_id":"8f2f..."}'
```

如果人工要改正文，用 `edit`：

```bash
curl -N -X POST http://127.0.0.1:8012/reviews/stream \
  -H 'content-type: application/json' \
  -H 'x-session-id: email-session-001' \
  -H 'x-trace-id: 29d6c8a3-2d86-4f1c-bba1-58d55f52f3a9' \
  -H 'x-thread-id: email-thread-001' \
  -d '{
    "type": "edit",
    "review_id": "8f2f...",
    "to": "lin@example.com",
    "subject": "订单 A1002 物流更新说明",
    "body": "您好，您的订单 A1002 已发货，预计明天送达。物流页面可能稍后更新，建议明天再查看。"
  }'
```

如果人工拒绝发送：

```bash
curl -N -X POST http://127.0.0.1:8012/reviews/stream \
  -H 'content-type: application/json' \
  -H 'x-session-id: email-session-001' \
  -H 'x-trace-id: 29d6c8a3-2d86-4f1c-bba1-58d55f52f3a9' \
  -H 'x-thread-id: email-thread-001' \
  -d '{"type":"reject","review_id":"8f2f...","message":"客户信息还没确认，暂不发送。"}'
```

## 关键点

- `/drafts/stream` 是业务入口。它先返回 `request.started`，中断时返回 `review.required`。
- `/reviews/stream` 是人工审核入口。它先返回 `review.received`，再返回 `email.sent`、`email.cancelled` 或新的 `review.required`。
- 服务会把底层 stream 转成自己的 SSE 协议。调用方只依赖 `message.delta`、`tool.started`、`tool.finished`、`review.required`、`email.sent`、`email.cancelled` 和 `error`。
- `interrupt_on={"send_email": ...}` 让 `send_email` 进入人工审核流程。其他 tool 仍然正常执行。
- `/reviews/stream` 用 `Command(resume=...)` 把 `approve`、`edit` 或 `reject` 送回同一个 thread。
- `x-thread-id` 是恢复现场的关键。创建草稿和提交审核必须使用同一个 `thread_id`。
- `x-trace-id` 会进入 Langfuse trace。服务响应和 SSE event 返回 UUID 字符串，传给 Langfuse 时会转成 32 位 hex。
- Langfuse 根 span 记录服务输入和输出。LangChain callback 记录 agent 内部的模型调用、tool 调用和中断前后的运行过程。代码不把 Langfuse context manager 跨过 SSE `yield`，避免 OpenTelemetry context 在流式响应里错位。
- `review_id` 标识这次待审核动作。示例保留这个字段，真实服务还应该校验它是否匹配当前待审核任务。
- 示例使用内存 checkpointer。服务重启后，等待审核的 thread 会丢失。真实服务应该换成 PostgreSQL、Redis 或其他外部 checkpoint。
- `edit` 会替换 `send_email` 的参数，再继续执行原来的 tool。这样人工可以改正文，不需要让 agent 重新起草。

## 取舍

这个示例只审核 `send_email`。读取工单不需要人工确认，因为它只是内部读操作。

服务 API 没有直接暴露 DeepAgents 的内部 `Interrupt` 对象，只暴露稳定的 SSE event、`thread_id` 和 `email`。调用方不需要知道 LangGraph 怎么存 checkpoint。

示例没有加入登录、权限、超时处理和审核记录表。真实项目至少要记录审核人、审核时间、原始草稿、修改后内容和发送结果。超时任务也要有清理或提醒机制。
