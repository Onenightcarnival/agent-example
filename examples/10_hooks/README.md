# 10 hooks

## 场景

agent 会自己决定调用哪个 tool，但不是每个 tool 都应该被直接执行。

这个示例用 middleware hook 做 tool 调用前的权限检查。agent 有四个业务 tool：

- `read_doc`：读取内部文档。
- `search_web`：搜索公开信息。
- `send_email`：模拟发送邮件。
- `delete_file`：模拟删除文件。

运行时会传入 `user_role`。hook 读取 role、tool 名和参数，再决定放行或拒绝。被拒绝时，hook 不执行原 tool，而是返回一条带 `error` 状态的 `ToolMessage`。模型会看到这条 tool 结果，再给用户解释原因。

示例会跑三次：

- `guest` 读取文档，允许。
- `guest` 删除文件，拒绝。
- `admin` 删除 `/tmp/demo/` 下的文件，允许。

## 代码

见 [tool_permission_hooks.py](tool_permission_hooks.py)。

## 运行方式

先确认 `.env` 里有模型变量：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash
```

运行示例：

```bash
uv run --env-file .env python examples/10_hooks/tool_permission_hooks.py
```

命令会打印每次运行的最终回答和审计记录。审计记录来自 hook：

```text
role: guest
user: 删除 /tmp/demo/old-report.csv。
assistant: 删除被拒绝，原因是当前角色（guest）没有调用删除文件工具的权限。
audit:
- deny delete_file: role=guest 不允许调用 tool=delete_file
```

## 关键点

- `ToolPermissionMiddleware.wrap_tool_call(...)` 是 tool 调用前的拦截点。这里可以读取 `request.tool_call`、`request.runtime.context` 和原始 tool。
- 调用 `handler(request)` 表示放行。直接返回 `ToolMessage` 表示短路，不执行原 tool。
- `ROLE_TOOL_POLICY` 是静态权限表。示例用它说明 role 到 tool 的授权关系。
- `delete_file` 还检查参数，只允许处理 `/tmp/demo/` 下的路径。权限检查不只看 tool 名，也要看参数。
- `wrap_model_call(...)` 过滤 DeepAgents 内置工具。这样 trace 和审计记录只围绕本章定义的业务 tool。
- `audit_log` 放在 runtime context 里。示例用它打印审计记录，真实项目通常会写入日志或审计表。

## 取舍

这个示例只做静态权限表和路径前缀检查。真实项目可以把规则放到数据库、配置中心或权限服务里。

hook 适合处理权限、审计、限流、脱敏这类横向逻辑。业务流程仍然应该写在清楚的 tool、服务或编排代码里。不要把主要业务步骤藏进一串 hook。
