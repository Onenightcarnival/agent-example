# 文档说明

这个目录放 cookbook 的写作规范、模板和维护说明。

## Cookbook 分类

```text
00_model_setup
01_agent_loop
02_instructions
03_tools
04_workspace
05_state_and_context
06_planning
07_subagents
08_human_approval
09_runtime_boundaries
10_end_to_end_agents
```

分类按构建顺序排列。先跑通模型和最小 agent loop，再加入指令、工具、状态、workspace、子 agent、人工确认和运行边界。

## Recipe 文件建议

一个 recipe 目录通常包含：

```text
README.md
main.py
requirements.txt 或 pyproject.toml
.env.example
```

如果示例只需要一个脚本，也可以只保留 `README.md` 和 `main.py`。不要为了统一形式塞空文件。

## README 写法

每篇 recipe 的 README 建议包含：

- 场景
- 运行方式
- 代码说明
- 可替换组件
- 常见问题

读者应该能先看 README 跑起来，再回头读代码。
