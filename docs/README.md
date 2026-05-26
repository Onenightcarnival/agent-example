# 文档说明

这个目录放 cookbook 的写作规范、模板和维护说明。

## Cookbook 分类

```text
00_getting_started
01_core_concepts
02_tools
03_memory
04_rag
05_langgraph_workflows
06_multi_agent
07_planning
08_production
09_end_to_end_apps
```

分类按学习顺序排列。前面的章节帮助读者跑通基础能力，后面的章节组合多个能力，做更接近真实项目的 agent 应用。

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
