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
- [13_model_routing](13_model_routing/)：在模型调用前按任务难度切换 `flash` 和 `pro`。
- [14_dynamic_tool_headers](14_dynamic_tool_headers/)：把请求级 header 转发给 MCP tool。
- [15_opengauss_checkpoint_and_store](15_opengauss_checkpoint_and_store/)：预留 openGauss checkpoint 和 store 示例。
- [16_backend_to_db](16_backend_to_db/)：预留后端服务写入数据库示例。
- [17_langfuse_session_traces](17_langfuse_session_traces/)：用同一个 Langfuse session 聚合多轮独立 trace。
- [18_agent_error_handling](18_agent_error_handling/)：把 `invoke` 和 `stream` 的细分异常转成业务错误。
- [19_tool_argument_json](19_tool_argument_json/)：当 tool call 的 `arguments` 不是合法 JSON 时，返回模型可见的 tool 失败结果。
- [20_langgraph_deepagents_langfuse](20_langgraph_deepagents_langfuse/)：外层 LangGraph 调 DeepAgents 节点，并用 `session_id` 接入 Langfuse。

每个目录先给一个最小示例。新增示例时，尽量放进已有主题。如果一个示例跨多个主题，放到它最想讲清楚的主题下。
