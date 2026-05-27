# 11 career memory

## 场景

长期记忆可以按人力资源里的职业履历来理解。

一个人做过什么、踩过什么坑、有什么偏好，都会写进履历。换任务、换项目，甚至换公司后，这些信息仍然有用。

这个示例把场景放在客户成功团队。客户成功经理长期服务 Acme 这类 B2B SaaS 客户。她知道客户怎么沟通、上线前常出什么问题、哪些排查步骤不能跳过。

示例用 `PostgresStore` 保存一份“职业履历式 memory”。它预先写入四类信息：

- `profile`：稳定背景。比如长期负责客户上线、权限配置和工单升级。
- `preference`：客户偏好。比如 Acme 的运营负责人只看结论、时间点和下一步。
- `experience`：做过的事。比如 Acme 上线前常遇到角色权限和报表可见性问题。
- `lesson`：踩坑记录。比如处理权限问题时，先确认测试环境还是生产环境。

agent 收到新的客户请求后，先通过 tool 读取这份履历，再给客户成功经理处理建议。它只在信息能跨工单复用时，才写入长期记忆。

## 代码

见 [career_memory_store.py](career_memory_store.py)。

## 运行方式

先确认 `.env` 里有模型变量和 PostgreSQL 变量：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=deepagents
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SSLMODE=disable
```

运行示例：

```bash
uv run --env-file .env python examples/11_career_memory/career_memory_store.py
```

第一次运行会调用 `store.setup()` 创建 LangGraph store 表。示例会写入固定的履历记忆，再让 agent 用这些记忆处理一个客户请求。

## 关键点

- `PostgresStore` 是通用持久化 store，不等于 memory。memory 是它的一种用法。
- 示例把长期记忆建模成职业履历，namespace 形如 `("person", person_id, kind)`。
- `profile`、`preference`、`experience` 和 `lesson` 是示例里的履历分类，不是 LangGraph 强制要求。
- `recall_career_memory` 从 `runtime.store` 读取记忆。这个 store 来自 `create_deep_agent(..., store=store)`。
- `save_career_memory` 只保存能跨任务复用的信息。当前任务的临时事实不写入长期记忆。
- `PostgresStore` 保存跨 thread 的长期上下文。`PostgresSaver` 保存某个 thread 的 checkpoint。两者不要混用。

## 取舍

这个示例没有做 embedding 检索，只用 namespace 和 key 说明长期记忆怎么分层。这样读者先看清楚写入边界，再考虑语义检索。

职业履历模型适合保存稳定背景、偏好、经验和复盘结论。不适合保存每轮对话、每次任务输入和临时状态。那些信息放 messages、state、checkpoint 或业务表里更合适。

真实系统还需要补充记忆更新、覆盖和删除规则。比如客户联系人换了，要覆盖旧偏好；踩坑记录过期了，要降权或删除；敏感信息不应该写入长期记忆。
