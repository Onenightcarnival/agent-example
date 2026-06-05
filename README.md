# Agent Example

这个仓库收集 agent 应用的中文示例，从简单到复杂演示 agent 构建的过程。DeepAgents 是当前示例使用的实现库。

它不按 API 参数堆章节，而是按 agent 能力组织内容：先搭出能动起来的原始 agent，再把它扩成能承担工作的现代 agent。

## 适合谁

- 已经会写基础 Python，想系统学习 agent 应用的人
- 想理解 agent 如何组织 model、tool、state、memory、skill 和 sandbox 的人
- 想看 DeepAgents 如何落地这些概念的人
- 想看可运行示例，而不是只看零散代码片段的人

## 设计主线

这个仓库按四个阶段组织示例：先让 agent 动起来，再让它能承担工作，然后补上生产系统需要的工程能力，最后进入复杂任务和运行控制。

先用一个简单比喻串起这些概念：把 agent 当成一个要上岗的人。

| agent 概念 | 打工人比喻 | 这一块回答什么 |
| --- | --- | --- |
| `model` | 候选人的基础能力 | 它能不能胜任这份工作 |
| `system prompt` | JD | 它负责什么、边界在哪里 |
| `tools` / MCP | 外部系统权限 | 它上班时能用哪些系统 |
| `messages` | 当前对话 | 它怎么记住当前对话 |
| `state` | 当前工单现场 | 它手头这件事有哪些材料 |
| `memory` | 职业履历 | 哪些经验和偏好以后还会用到 |
| `skills` | 可迁移技能 | 哪些做法可以变成稳定技能 |
| `sandbox` | 工作电脑 | 它的文件、依赖和半成品放在哪里 |
| `checkpoint` | 运行现场快照 | 它中断后怎么回到刚才的工作 |
| `observability` | 工作记录 | 怎么看它刚才具体做了什么 |
| `hooks` | 公司制度 | 哪些动作要先过规则和权限 |
| HITL | 主管审批 | 哪些动作要交给人确认 |
| service | 接入业务系统 | 业务系统怎么把任务交给它 |

第一阶段是原始 agent，回答“agent 怎么动起来”。

1. `model`：接入大模型，确认模型配置能被 agent 使用。
2. `tools_mcp`：工具和 MCP 让 agent 操作外部世界。
3. `turns`：用 `messages` 串起多轮对话。

第二阶段是现代 agent，回答“agent 怎么变成工作单元”。

4. `memory`：system prompt 像 JD，长期记忆像履历，`state` 像当前工单上下文。
5. `skills`：skill 把稳定做法沉到文件里，让 agent 可以复用。
6. `sandbox`：sandbox 是 agent 的办公电脑，负责文件、命令和权限边界。

第三阶段是生产 agent，回答“agent 怎么接进真实系统”。

7. `persistence`：把运行状态放到外部存储，让 agent 可以恢复现场。
8. `observability`：记录模型、tool 和 state 的变化，让问题可以定位。
9. `service_integration`：把 agent 包成服务，接入业务请求、任务状态和错误处理。

第四阶段是进阶 agent，回答“复杂任务怎么控制和扩展”。

10. `hooks`：在关键步骤插入自定义逻辑，接入权限、记录和业务规则。
11. `career_memory`：用职业履历模型组织长期记忆，区分偏好、经验和踩坑记录。
12. `hitl`：在关键节点加入人工确认、打断和继续。
13. `model_routing`：按任务难度在 `flash` 和 `pro` 之间切换。
14. `dynamic_tool_headers`：把请求里的身份 header 转发给 MCP tool。
15. `opengauss_checkpoint_and_store`：预留 openGauss checkpoint 和 store 示例。
16. `backend_to_db`：预留后端服务写入数据库示例。
17. `langfuse_session_traces`：用同一个 Langfuse session 聚合多轮独立 trace。
18. `agent_error_handling`：用 middleware 捕获运行期异常，再转成业务错误。

## 内容结构

```text
examples/
  01_model/                 原始 agent：模型
  02_tools_mcp/             原始 agent：工具与 MCP
  03_turns/                 原始 agent：多轮对话
  04_memory/                现代 agent：记忆
  05_skills/                现代 agent：技能
  06_sandbox/               现代 agent：办公环境
  07_persistence/           生产 agent：外置持久化
  08_observability/         生产 agent：可观测
  09_service_integration/   生产 agent：服务化集成
  10_hooks/                 进阶 agent：自定义 hooks
  11_career_memory/         进阶 agent：职业履历式记忆
  12_hitl/                  进阶 agent：human in the loop
  13_model_routing/         进阶 agent：模型路由
  14_dynamic_tool_headers/  进阶 agent：动态 tool header
  15_opengauss_checkpoint_and_store/ 生产 agent：openGauss checkpoint 和 store（占位）
  16_backend_to_db/         生产 agent：后端服务写入数据库（占位）
  17_langfuse_session_traces/ 生产 agent：Langfuse session 与 trace
  18_agent_error_handling/  生产 agent：运行期异常处理
docs/
  README.md                 写作约定和目录说明
  example-template.md       示例模板
```

每个主题目录先给一个最小示例。新增内容时，优先放到已有主题下。如果一个示例跨多个主题，放到它最想讲清楚的主题里。

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

示例代码会同时传入两个 `extra_body` 参数。
DeepSeek 使用 `thinking` 关闭 thinking。
有些自部署模型服务使用 `chat_template_kwargs` 关闭 chat template thinking。

```python
extra_body={
    "thinking": {"type": "disabled"},  # DeepSeek：关闭 thinking。
    "chat_template_kwargs": {"enable_thinking": False},  # 自部署模型服务：关闭 chat template thinking。
},
```

有些示例需要本地服务。这里假设你已经会使用 Docker 和 Docker Compose。

- AIO Sandbox：使用官方仓库里的 [docker-compose.yaml](https://github.com/agent-infra/sandbox/blob/main/docker-compose.yaml)，默认 MCP 地址是 `http://localhost:8080/mcp`。如果服务需要鉴权，在 `.env` 里设置 `SANDBOX_MCP_AUTH_HEADER`。
- Langfuse：需要观测示例时，使用官方仓库里的 [docker-compose.yml](https://github.com/langfuse/langfuse/blob/main/docker-compose.yml)。启动后把 `.env` 里的 Langfuse 变量改成你的本地配置。
- PostgreSQL with pgvector：需要持久化、记忆或检索示例时，准备一个带 pgvector 扩展的 PostgreSQL。可以参考 [pgvector Docker 镜像说明](https://github.com/pgvector/pgvector#docker)，用 `pgvector/pgvector` 镜像写一个最小 compose 服务。

## 运行示例

每个示例的 README 都会写运行命令。比如：

```bash
uv run --env-file .env python examples/01_model/model_connection.py
```

示例代码尽量小，只保留说明问题所需的部分。需要外部服务、模型调用或额外环境变量时，会在对应 README 里说明。

## 写作方式

每篇示例按这个顺序写：

1. 场景：这个示例解决什么问题
2. 代码：可以直接运行的最小实现
3. 运行方式：命令、环境变量和预期输出
4. 关键点：agent 概念、DeepAgents 对象和运行行为
5. 取舍：适合什么，不适合什么

## 参与方式

欢迎提交新的示例、修正文档和补充运行说明。写作风格见 [CONTRIBUTING.md](CONTRIBUTING.md)，目录约定见 [docs/README.md](docs/README.md)。
