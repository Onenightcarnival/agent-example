# 05 skills

## 场景

有些能力会反复用到，比如审稿、生成 changelog、整理调研结果。

这类稳定做法适合写成 skill。skill 不是一次性的 prompt，而是一份可加载的操作说明。

## 代码

见 [skill_agent.py](skill_agent.py) 和 [skills/recipe_reviewer/SKILL.md](skills/recipe_reviewer/SKILL.md)。

## 运行方式

```bash
uv run --env-file .env python cookbook/05_skills/skill_agent.py
```

## 关键点

- `skills` 接收 skill 来源目录列表。
- `FilesystemBackend` 让示例直接从本地 recipe 目录读取 skill 文件。
- skill 目录里放 `SKILL.md`。
- 多个 agent 或 subagent 可以复用同一组 skill。

## 取舍

skill 适合稳定流程。不适合放一次性需求。一次性需求放用户消息里更清楚。
