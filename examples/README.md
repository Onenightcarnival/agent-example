# Examples

这里按四个阶段组织 agent 示例。当前代码用 DeepAgents 演示这些概念。

第一阶段是原始 agent：

- [01_model](01_model/)：接入模型，确认模型配置能被 agent 使用。
- [02_tools_mcp](02_tools_mcp/)：给 agent 增加本地 tool 和 MCP tool。
- [03_turns](03_turns/)：用 `messages` 串起多轮对话。

第二阶段是现代 agent：

- [04_memory](04_memory/)：把提示词、长期记忆和当前 state 分开看。
- [05_skills](05_skills/)：把稳定做法写成 skill，让 agent 复用。
- [06_sandbox](06_sandbox/)：让 agent 通过远程 sandbox 处理文件和命令。

第三阶段是生产 agent：

- [07_persistence](07_persistence/)：把运行状态放到外部存储，让 agent 可以恢复现场。
- [08_observability](08_observability/)：记录模型、tool 和 state 的变化，让问题可以定位。
- [09_service_integration](09_service_integration/)：把 agent 包成服务，接入业务请求、任务状态和错误处理。

第四阶段是进阶 agent：

- [10_hooks](10_hooks/)：在 tool 调用前做权限检查和审计记录。
- [11_career_memory](11_career_memory/)：用职业履历模型组织长期记忆。
- [12_hitl](12_hitl/)：在关键节点加入人工确认、打断和继续。

每个目录先给一个最小示例。新增示例时，尽量放进已有主题。如果一个示例跨多个主题，放到它最想讲清楚的主题下。
