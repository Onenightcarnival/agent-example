# 01 model

## 场景

先跑通最小 agent。

这个示例只设置模型和 system prompt，不加业务 tool。DeepAgents 仍会带上默认工具，比如 todo 和文件工具。这里先不使用它们，只看 agent 如何接收任务并返回结果。

## 代码

见 [minimal_agent.py](minimal_agent.py)。

## 运行方式

先在 `.env` 里设置模型。

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash
```

运行：

```bash
uv run --env-file .env python cookbook/01_model/minimal_agent.py
```

## 关键点

- `create_deep_agent` 创建一个可执行的 LangGraph graph。
- `model` 可以用 `provider:model` 字符串，也可以传已经初始化好的 chat model。
- `system_prompt` 像岗位说明。它告诉 agent 该怎么工作，而不是把所有上下文都塞进用户消息。

## 取舍

这个 recipe 适合检查模型配置是否能跑通。它不适合展示工具调用、文件读写或长期任务。
