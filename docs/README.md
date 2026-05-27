# 文档维护说明

这个项目按“四阶段、十二主题”维护 agent 示例。当前可运行示例使用 DeepAgents。

## 目录

```text
examples/
  01_model/
  02_tools_mcp/
  03_turns/
  04_memory/
  05_skills/
  06_sandbox/
  07_persistence/
  08_observability/
  09_service_integration/
  10_hooks/
  11_career_memory/
  12_hitl/
docs/
  README.md
  example-template.md
```

## 主题边界

第一阶段是原始 agent：

- `01_model`：模型接入、模型配置、OpenAI 兼容接口。
- `02_tools_mcp`：本地 tool、MCP tool、外部系统调用。
- `03_turns`：conversation、turn、messages 上下文。

第二阶段是现代 agent：

- `04_memory`：system prompt、长期 memory、短期 state。
- `05_skills`：skill 文件、skill 复用、subagent 使用 skill。
- `06_sandbox`：文件系统、命令执行、权限、运行边界。

第三阶段是生产 agent：

- `07_persistence`：外置持久化、checkpoint、thread 恢复。
- `08_observability`：日志、trace、tool 调用记录、状态快照、失败定位。
- `09_service_integration`：API 封装、任务状态、错误处理、服务边界。

第四阶段是进阶 agent：

- `10_hooks`：模型调用、tool 调用和状态更新前后的自定义逻辑。
- `11_career_memory`：职业履历式长期记忆、客户偏好、经验和踩坑记录。
- `12_hitl`：人工确认、审批、打断、继续和结果修正。

如果一个示例同时涉及多个主题，放到它最想讲清楚的主题。不要为了分类新建很细的目录。

## 示例结构

每篇示例使用这个顺序：

1. 场景
2. 代码
3. 运行方式
4. 关键点
5. 取舍

示例代码要小，但要能说明行为。README 负责解释上下文，代码文件负责演示行为。

## 写作检查

提交前读一遍中文说明，重点看这些问题：

- 有没有空泛判断
- 有没有翻译腔
- 有没有互联网黑话
- 有没有句子太长
- 代码和运行命令是否一致
- 环境变量是否写全
