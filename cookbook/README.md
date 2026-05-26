# Cookbook

这里按两个阶段组织 DeepAgents recipe。

第一阶段是原始 agent：

- [01_model](01_model/)：接入模型，确认模型配置能被 DeepAgents 使用。
- [02_tools_mcp](02_tools_mcp/)：给 agent 增加本地 tool 和 MCP tool。
- [03_turns](03_turns/)：用 `messages` 串起多轮对话。

第二阶段是现代 agent：

- [04_memory](04_memory/)：把提示词、长期记忆和当前 state 分开看。
- [05_skills](05_skills/)：把稳定做法写成 skill，让 agent 复用。
- [06_sandbox](06_sandbox/)：让 agent 在受控文件系统里工作。

每个目录先给一个最小示例。新增 recipe 时，尽量放进已有主题。如果一个示例跨多个主题，放到它最想讲清楚的主题下。
