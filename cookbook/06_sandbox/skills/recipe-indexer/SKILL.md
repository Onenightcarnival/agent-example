---
name: recipe-indexer
description: 整理 DeepAgents Cookbook 的 recipe notes，生成一份按章节排列的 Markdown 索引。需要处理 recipe 目录、章节摘要或 cookbook 大纲时使用。
metadata:
  short-description: 生成 cookbook recipe 索引
---

# Recipe Indexer

用这个 skill 把零散的 recipe notes 整理成索引。

## 使用方式

运行随 skill 分发的 Python 脚本：

```bash
cd /home/gem/workspace/deepagents-cookbook/skills/recipe-indexer
uv run --no-dev python scripts/build_recipe_index.py \
  /home/gem/workspace/deepagents-cookbook/input/recipe_notes.md \
  /home/gem/workspace/deepagents-cookbook/output/recipe_index.md
```

脚本只依赖 Python 标准库。Python 版本要求见 `pyproject.toml`。

它会读取 Markdown 列表，输出：

- 标题
- 每章一行索引
- 原始 notes 数量

## 验证

在 skill 根目录运行：

```bash
uv run --no-dev python scripts/check.py
uv run pytest
uv run ruff check .
```

## 注意

- 不要改输入文件。
- 输出目录不存在时，先创建目录。
- 如果输入里没有 recipe 条目，仍然写出空索引。
- 不需要网络。
- 不需要额外环境变量。
