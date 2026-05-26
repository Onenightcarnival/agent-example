# Agent Cookbook

这个仓库收集 agent 应用的中文 recipe。DeepAgents 是当前示例使用的实现库。

它不按 API 参数堆章节，而是按 agent 能力组织内容：先搭出能动起来的原始 agent，再把它扩成能承担工作的现代 agent。

## 适合谁

- 已经会写基础 Python，想系统学习 agent 应用的人
- 想理解 agent 如何组织 model、tool、state、memory、skill 和 sandbox 的人
- 想看 DeepAgents 如何落地这些概念的人
- 想看可运行示例，而不是只看零散代码片段的人

## 设计主线

第一阶段是原始 agent，回答“agent 怎么动起来”。

1. `model`：接入大模型，确认模型配置能被 agent 使用。
2. `tools_mcp`：工具和 MCP 让 agent 操作外部世界。
3. `turns`：用 `messages` 串起多轮对话。

第二阶段是现代 agent，回答“agent 怎么变成工作单元”。

4. `memory`：system prompt 像 JD，长期记忆像履历，`state` 像当前工单上下文。
5. `skills`：skill 把稳定做法沉到文件里，让 agent 可以复用。
6. `sandbox`：sandbox 是 agent 的办公电脑，负责文件、命令和权限边界。

## 内容结构

```text
cookbook/
  01_model/                 原始 agent：模型
  02_tools_mcp/             原始 agent：工具与 MCP
  03_turns/                 原始 agent：多轮对话
  04_memory/                现代 agent：记忆
  05_skills/                现代 agent：技能
  06_sandbox/               现代 agent：办公环境
docs/
  README.md                 写作约定和目录说明
  recipe-template.md        recipe 模板
```

每个主题目录先给一个最小 recipe。后续新增内容时，优先放到这六个主题下。

## 本地环境

项目使用 `uv` 管理 Python 环境。

```bash
uv sync
```

复制 `.env.example`，填入模型配置。

```bash
cp .env.example .env
```

常用变量：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash
```

示例默认使用 DeepSeek 的 OpenAI 兼容接口。换模型时，改这三个变量即可。

## 运行示例

每个 recipe 的 README 都会写运行命令。比如：

```bash
uv run --env-file .env python cookbook/01_model/model_connection.py
```

示例代码尽量小，只保留说明问题所需的部分。需要外部服务、模型调用或额外环境变量时，会在对应 README 里说明。

## 写作方式

每篇 recipe 按这个顺序写：

1. 场景：这个示例解决什么问题
2. 代码：可以直接运行的最小实现
3. 运行方式：命令、环境变量和预期输出
4. 关键点：agent 概念、DeepAgents 对象和运行行为
5. 取舍：适合什么，不适合什么

## 参与方式

欢迎提交新的 recipe、修正文档和补充运行说明。写作风格见 [CONTRIBUTING.md](CONTRIBUTING.md)，目录约定见 [docs/README.md](docs/README.md)。
