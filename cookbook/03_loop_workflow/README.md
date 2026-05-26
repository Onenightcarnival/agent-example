# 03 loop_workflow

## 场景

真实任务通常不是一次回答结束。agent 需要先规划，再执行，再根据结果调整。

这个示例让 agent 写一个短待办，并用 tool 检查任务标题是否太长。它展示 loop 的位置：模型决定下一步，tool 返回观察结果，agent 再继续。

## 代码

见 [todo_loop.py](todo_loop.py)。

## 运行方式

```bash
uv run --env-file .env python cookbook/03_loop_workflow/todo_loop.py
```

## 关键点

- DeepAgents 会在一次 `invoke` 内部处理多轮 model 和 tool 调用。
- tool 的返回值会进入下一轮上下文。
- 如果步骤必须固定，优先写 workflow。如果步骤要靠观察结果调整，保留 agent loop。

## 取舍

loop 适合开放任务，比如排查、写作和资料整理。workflow 适合审批、表单处理和固定交付流程。
