# Cookbook

这里放 DeepAgents 的示例代码和配套说明。

## 目录

- `00_model_setup/`：模型配置、环境变量、DeepSeek 接入和 streaming。
- `01_agent_loop/`：最小 agent loop、停止条件、循环错误恢复。
- `02_instructions/`：system prompt、任务指令、输出格式和工具使用规则。
- `03_tools/`：自定义工具、工具参数、工具返回和错误处理。
- `04_workspace/`：读文件、写文件、修改文件和维护中间产物。
- `05_state_and_context/`：消息历史、任务状态、工具结果和上下文裁剪。
- `06_planning/`：任务拆解、todo 更新、失败步骤修复和最终检查。
- `07_subagents/`：主 agent 分派任务、子 agent 上下文边界和结果合并。
- `08_human_approval/`：暂停、确认、拒绝后改计划和恢复执行。
- `09_runtime_boundaries/`：最大步数、超时、重试、工具限制和成本边界。
- `10_end_to_end_agents/`：研究、代码编辑、文档写作和数据分析 agent。

先从 `00_model_setup/` 和 `01_agent_loop/` 开始补示例。每个分类目录里保留一个 README，用来索引该分类下的 recipe。
