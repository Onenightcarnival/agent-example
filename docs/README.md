# 文档维护说明

这个项目按“二阶段、六主题”维护 cookbook。

## 目录

```text
cookbook/
  01_model/
  02_tools_mcp/
  03_loop_workflow/
  04_memory/
  05_skills/
  06_sandbox/
docs/
  README.md
  recipe-template.md
```

## 主题边界

- `01_model`：模型接入、模型配置、OpenAI 兼容接口。
- `02_tools_mcp`：本地 tool、MCP tool、外部系统调用。
- `03_loop_workflow`：agent loop、固定 workflow、停止条件。
- `04_memory`：system prompt、长期 memory、短期 state、checkpoint。
- `05_skills`：skill 文件、skill 复用、subagent 使用 skill。
- `06_sandbox`：文件系统、命令执行、权限、运行边界。

如果一个 recipe 同时涉及多个主题，放到它最想讲清楚的主题。不要为了分类新建很细的目录。

## Recipe 结构

每篇 recipe 使用这个顺序：

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
