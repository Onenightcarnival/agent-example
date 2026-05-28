# 05 skills

## 场景

skill 是 agent 会的具体技能，就像简历上的一条能力。

一个人可以会做 PPT、写 SQL、爬数据、做财报。agent 也可以加载这类技能。每个 skill 对应一份可复用的操作说明。

## 代码

见 [skill_agent.py](skill_agent.py) 和 [skills/example-reviewer/SKILL.md](skills/example-reviewer/SKILL.md)。

示例只问 agent 当前有哪些 skill 可用。这样可以先确认 skill 已经挂到框架里。

## 运行方式

```bash
uv run --env-file .env python examples/05_skills/skill_agent.py
```

## 关键点

- `skills` 接收 skill 来源目录列表。
- `FilesystemBackend` 让示例直接从本地示例目录读取 skill 文件。
- 一个 skill 对应一个目录，目录里放 `SKILL.md`。
- skill 名称用小写字母、数字和连字符，比如 `example-reviewer`。
- 多个 agent 或 subagent 可以复用同一组 skill。

## 取舍

skill 适合描述长期能力。不适合放一次性需求。一次性需求放用户消息里更清楚。
