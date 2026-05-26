# 04 memory

## 场景

一次对话里的上下文不等于长期记忆。

这个示例把三类信息分开：

- system prompt：当前岗位说明，类似 JD。
- memory：长期偏好和工作约定，类似履历。
- state：当前这次运行里的消息和文件。

## 代码

见 [memory_agent.py](memory_agent.py) 和 [memory/AGENTS.md](memory/AGENTS.md)。

## 运行方式

```bash
uv run --env-file .env python cookbook/04_memory/memory_agent.py
```

## 关键点

- `memory` 接收 `AGENTS.md` 文件路径列表。
- `FilesystemBackend` 让示例直接从本地 recipe 目录读取 memory 文件。
- memory 会在 agent 启动时加入系统上下文。
- 适合放稳定偏好、项目约定和长期角色信息。

## 取舍

不要把临时任务塞进 memory。临时信息放用户消息、`state` 或输入文件里。memory 越稳定，越容易复用。
