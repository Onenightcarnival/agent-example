# Agent Loop

这一章用 DeepAgents 跑通最小 agent loop：接收任务、调用模型、必要时调用工具，再把结果放回消息循环。

## 运行

```bash
uv run python cookbook/01_agent_loop/minimal_agent.py
uv run python cookbook/01_agent_loop/tool_loop.py
```

## 文件

- `minimal_agent.py`：没有自定义工具的最小 agent。
- `tool_loop.py`：agent 先调用工具，再根据工具结果回答。

## 说明

两个脚本都从根目录 `.env` 读取 `MODEL_BASE_URL`、`MODEL_API_KEY`、`MODEL_NAME`。

`tool_loop.py` 关闭了 DeepSeek thinking：

```python
extra_body={"thinking": {"type": "disabled"}}
```

DeepSeek thinking 模式下，多轮工具调用需要把 `reasoning_content` 带回 API。这个示例先避开这件事，只看 agent loop 本身。
