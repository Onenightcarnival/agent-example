# DeepAgents Cookbook

这个仓库收集 DeepAgents 的中文示例。内容聚焦 DeepAgents 这一层：agent loop、指令、工具、状态、workspace、子 agent、人工确认和运行边界。

它不是 API 文档的翻译，也不是把所有参数列一遍。每篇 recipe 都从一个具体问题开始，给出可运行代码，再解释关键取舍。

## 适合谁

- 已经会写基础 Python，想系统学习 agent 应用的人
- 想从零构建 agent，并理解 DeepAgents 如何组织任务、工具和状态的人
- 想看完整示例，而不是只看零散代码片段的人

## 内容结构

```text
cookbook/
  00_model_setup/            模型配置
  01_agent_loop/             Agent loop
  02_instructions/           指令组织
  03_tools/                  工具调用
  04_workspace/              Workspace 与文件
  05_state_and_context/      状态与上下文
  06_planning/               任务规划
  07_subagents/              子 agent
  08_human_approval/         人工确认
  09_runtime_boundaries/     运行边界
  10_end_to_end_agents/      完整 agent
docs/
  README.md                  写作约定和目录说明
  recipe-template.md         recipe 模板
```

## 本地环境

项目使用 `uv` 管理 Python 环境。

```bash
uv sync
```

每个 recipe 会在自己的 README 里写运行命令。如果示例需要额外依赖，再用 `uv add` 加到项目里。

## 每篇 recipe 怎么写

每篇 recipe 尽量包含这些部分：

- 场景：这个示例解决什么问题
- 代码：可以直接运行的最小实现
- 解释：关键对象、状态、工具和流程
- 变体：可以替换的模型、工具、指令或运行边界
- 常见坑：容易出错的地方和排查方式

## 当前状态

项目刚初始化，内容还在规划中。优先补齐这些方向：

- DeepSeek 模型配置
- 最小 agent loop
- 指令和停止条件
- 自定义工具调用
- workspace 文件读写
- subagent 分工示例

## 参与方式

欢迎提交新的 recipe、修正文档和补充运行说明。写作风格见 [CONTRIBUTING.md](CONTRIBUTING.md)，目录约定见 [docs/README.md](docs/README.md)。
