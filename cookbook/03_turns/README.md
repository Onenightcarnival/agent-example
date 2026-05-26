# 03 turns

## 场景

真实对话不是一次回答结束。

用户第一轮只说一个模糊想法。assistant 先追问。用户第二轮补充场景。assistant 再追问。等信息够了，assistant 才整理成 recipe brief。

这里先讲 `turn`：

- 一个 `turn` 是用户输入一次，assistant 回复一次。
- 多个 `turn` 组成一段 conversation。
- 下一轮要接住上一轮上下文，就要把前面的 `messages` 继续传给 agent。

## 代码

见 [conversation_turns.py](conversation_turns.py)。

## 运行方式

先设置模型环境变量，沿用第一章：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-pro
```

运行：

```bash
uv run --env-file .env python cookbook/03_turns/conversation_turns.py
```

## 关键点

- 示例用三条预设用户输入模拟三轮对话。
- 每次调用 `agent.invoke(...)` 都代表一个新的 `turn`。
- `result["messages"]` 会带上这一轮后的对话上下文。
- 下一轮调用时，把上一次的 `messages` 传回去，agent 才知道用户前面说过什么。
- 如果不传旧 `messages`，下一轮就是一次新的独立对话。

## 取舍

`messages` 适合保存当前 conversation 里的上下文，比如用户刚补充的需求、assistant 刚追问的问题。

不要把所有信息都塞进 `messages`。跨 conversation 仍然有用的偏好，放到 memory。需要恢复很长的运行过程，再考虑 checkpoint。
