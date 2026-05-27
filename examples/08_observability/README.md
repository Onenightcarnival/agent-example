# 08 observability

## 场景

agent 接入工具后，只看最后一句回答通常不够。

这个示例演示如何把一次 DeepAgents 运行发送到 Langfuse。代码不改 agent 的行为，只在运行时挂一个 Langfuse callback。

用户询问订单 `A1002` 的状态。agent 会调用本地工具查询订单，再生成一句回复。运行结束后，可以在 Langfuse 里看到这次请求的 trace，包括模型调用、tool 调用、输入输出和耗时。

## 代码

见 [langfuse_observability.py](langfuse_observability.py)。

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
uv run --env-file .env python examples/08_observability/langfuse_observability.py
```

命令会打印 agent 的最后一句回复。随后打开 Langfuse 项目，在 traces 里查看 `langfuse_observability_demo`。

## 关键点

- `Langfuse(...)` 会显式传入 `public_key`、`secret_key` 和 `base_url`。示例从环境变量读取这些值。
- `CallbackHandler` 来自 `langfuse.langchain`。DeepAgents 基于 LangGraph / LangChain 运行，所以可以用 LangChain callback 接入 Langfuse。
- `agent.invoke(..., config={"callbacks": [langfuse_handler]})` 是接入点。agent 创建逻辑和工具逻辑不需要为了 tracing 改写。
- `DisableBuiltinTools` 会过滤 DeepAgents 内置工具，让这次 trace 只展示订单查询工具。
- `run_name` 会显示在 Langfuse trace 里，适合标记这类示例运行。
- `metadata` 和 `tags` 可以记录示例名、环境、版本或业务 id。不要把密钥、完整用户隐私或敏感业务数据放进去。
- 短脚本退出前调用 `langfuse.flush()`，避免 trace 还没发送完进程就结束。

## 取舍

这个示例只演示无侵入式 tracing。它适合回答“这次运行发生了什么”：模型收到了什么、tool 传入了什么、哪一步慢、哪一步报错。

生产环境还需要处理采样、脱敏、保留周期和告警。Langfuse trace 也不能替代业务日志。订单状态、请求状态和审计记录仍然应该写到业务系统里。
