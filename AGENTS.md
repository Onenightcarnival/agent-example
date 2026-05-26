# AGENTS.md

这个仓库是中文 Agent Cookbook。DeepAgents 是当前实现实例。请把它当成给开发者看的技术项目来维护。

## 写作约定

- 全站默认使用中文。
- 保留必要英文术语，比如 `agent`、`tool`、`state`、`checkpoint`、`retriever`。
- 不写营销话术，不堆“高效、智能、完整、领先”这类形容词。
- 句子尽量短。能直接说做法，就不要绕成“通过 A 实现 B”。
- 每篇 recipe 先讲场景，再给代码，最后解释取舍。
- 示例代码要尽量小，但必须能说明问题。

## 目录约定

- `cookbook/` 放可运行示例和配套说明。
- `docs/` 放项目说明、写作模板和维护文档。
- 一个 recipe 尽量独立成目录，目录名用英文小写和下划线。
- README 负责串起上下文，代码文件负责演示行为。

## 改动原则

- 优先沿用现有目录和命名。
- 不为了抽象而抽象。只有多个 recipe 真的复用同一段逻辑时，再提公共 helper。
- 不提交本地编辑器文件、缓存文件、密钥或运行产物。
- 新增示例时，同步补充运行方式和环境变量说明。
- 修改已有 recipe 时，确认 README、代码和依赖说明仍然一致。

## 提交约定

- commit message 使用 Conventional Commits 风格。
- 常用类型包括 `docs`、`feat`、`fix`、`chore`、`refactor`、`test`。
- 标题格式为 `<type>: <summary>`，summary 用英文小写开头，尽量控制在 50 个字符内。
- 标题示例：`docs: add recipe template`、`chore: add ruff config`、`fix: update tool example env vars`。
- 需要正文时，空一行后说明改了什么、为什么改。不要写“本次提交主要用于优化项目结构”这类空话。
- AI 助手参与提交时，在 commit message 末尾添加自己为 co-author。

## 中文审稿清单

提交前读一遍文档，检查这些问题：

- 有没有空泛判断，比如“带来更好的体验”
- 有没有翻译腔，比如“对于开发者而言”
- 有没有互联网黑话，比如“赋能、闭环、链路、底座”
- 有没有过长句，可以拆成两句
- 有没有解释动机太多，却没说清楚读者怎么做
