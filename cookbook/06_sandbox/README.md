# 06 sandbox

## 场景

agent 要完成工作，通常需要文件和命令。sandbox 给它一个受控办公环境。

这个示例让 agent 读取输入文件，并把整理后的结果写到输出文件。权限只允许写 `/workspace/**`。
示例会创建临时目录，运行结束后不在仓库里留下产物。

## 代码

见 [sandbox_agent.py](sandbox_agent.py)。

## 运行方式

```bash
uv run --env-file .env python cookbook/06_sandbox/sandbox_agent.py
```

## 关键点

- `FilesystemBackend` 把 agent 文件操作落到指定目录。
- `FilesystemPermission` 可以限制读写范围。
- sandbox 边界要和任务边界一致。能只给工作目录，就不要给整个项目。

## 取舍

sandbox 适合让 agent 做可验证的文件任务。它不替代代码 review，也不替代人工审批。涉及删除、发布或外部写入时，仍要加确认步骤。
