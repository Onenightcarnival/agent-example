# DeepAgents Cookbook

这个仓库收集 DeepAgents 的中文示例。内容会覆盖 DeepAgents 本身，也会穿插 LangChain、LangGraph 里常用的组件和写法。

它不是 API 文档的翻译，也不是把所有参数列一遍。每篇 recipe 都从一个具体问题开始，给出可运行代码，再解释关键取舍。

## 适合谁

- 已经会写基础 Python，想系统学习 agent 应用的人
- 用过 LangChain 或 LangGraph，但还没把它们和 DeepAgents 放在一起用的人
- 想看完整示例，而不是只看零散代码片段的人

## 内容结构

```text
cookbook/
  00_getting_started/        快速开始
  01_core_concepts/          核心概念
  02_tools/                  工具调用
  03_memory/                 记忆与上下文
  04_rag/                    RAG 与知识库
  05_langgraph_workflows/    LangGraph 工作流
  06_multi_agent/            多 agent 协作
  07_planning/               任务规划与执行
  08_production/             生产化
  09_end_to_end_apps/        完整应用
docs/
  README.md                  写作约定和目录说明
  recipe-template.md         recipe 模板
```

## 本地运行

项目使用 `uv` 管理 Python 环境。

```bash
uv run python main.py
```

新增 recipe 时，优先在对应目录里写清楚运行命令。如果示例需要额外依赖，再用 `uv add` 加到项目里。

## 每篇 recipe 怎么写

每篇 recipe 尽量包含这些部分：

- 场景：这个示例解决什么问题
- 代码：可以直接运行的最小实现
- 解释：关键对象、状态、工具和流程
- 变体：可以替换的模型、工具、存储或图结构
- 常见坑：容易出错的地方和排查方式

## 当前状态

项目刚初始化，内容还在规划中。优先补齐这些方向：

- 最小 DeepAgents 示例
- 自定义工具调用
- DeepAgents 接入 LangGraph node
- 带检索的知识库问答
- supervisor-worker 多 agent 示例

## 参与方式

欢迎提交新的 recipe、修正文档和补充运行说明。写作风格见 [CONTRIBUTING.md](CONTRIBUTING.md)，目录约定见 [docs/README.md](docs/README.md)。
