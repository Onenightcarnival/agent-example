# Recipe 标题

## 场景

用两三句话说明读者遇到什么问题。先讲任务，不要先讲概念。

## 代码

说明示例文件的位置。

```text
cookbook/主题目录/recipe_name/
```

如果只有一个 Python 文件，也可以直接链接到文件。

## 运行方式

列出必要环境变量。默认写在 `.env` 里。

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash
```

给出运行命令。

```bash
uv run --env-file .env python cookbook/主题目录/example.py
```

如果需要额外服务、MCP server 或本地文件，在这里写清楚。

## 关键点

- 先说明这个 recipe 里最重要的 agent 概念。
- 再说明对应的 DeepAgents 对象。
- 说明输入、输出和状态变化。
- 说明 tool、memory、skill 或 sandbox 的边界。

## 取舍

写清楚这个做法适合什么，不适合什么。不要写“提升体验”这类空话。
