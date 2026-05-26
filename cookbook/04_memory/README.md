# 04 memory

## 场景

一次对话里的上下文不等于长期记忆。

这个示例用“写 JD”说明三类信息：

- system prompt：当前岗位说明，类似 JD。它规定 agent 这次扮演什么角色。
- memory：长期记忆，类似职业履历。它记录这个人做过什么、踩过什么坑、客户偏好是什么。
- state：当前这次运行里的消息和文件，类似当前工单上下文。

长期记忆可以跟着人走。换一个任务，甚至换一家公司，职业履历里的经验仍然能复用。

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
- 适合放稳定履历、项目经验、踩坑记录和客户偏好。

## 取舍

不要把临时任务塞进 memory。临时信息放用户消息、`state` 或输入文件里。

`AGENTS.md` 只是这个示例里的持久化文件。真实系统可以把长期记忆放到数据库、对象存储或用户自己的文件里。关键不是存在哪里，而是把“长期会用到的职业履历”和“这次才有的上下文”分开。
