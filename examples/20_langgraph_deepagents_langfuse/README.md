# 20 langgraph_deepagents_langfuse

## 场景

有些系统已经用 LangGraph 编排流程。比如先判断请求类型，再把订单问题交给一个 agent，最后判断是否需要人工处理。

这个示例演示最小接法：

- 最外层是 LangGraph。
- 中间一个节点调用 DeepAgents。
- 每次运行生成一个新的 `session_id`。
- Langfuse 用同一个 `session_id` 聚合 trace。
- LangGraph 用这个 `session_id` 派生 `thread_id`。

DeepAgents 的创建逻辑、tool 和提示词不需要为了 Langfuse 改写。只要在运行时传入 `config`。

## 代码

见 [langgraph_deepagents_langfuse.py](langgraph_deepagents_langfuse.py)。

核心是 DeepAgents 节点接收外层 LangGraph 传进来的 `config`，再原样传给 `order_agent.invoke(...)`：

```python
def call_deepagents(state: GraphState, config: RunnableConfig) -> GraphState:
    result = order_agent.invoke(
        {"messages": [{"role": "user", "content": state["question"]}]},
        config=config,
    )
    return {"answer": result["messages"][-1].content}
```

入口生成一个 UUID 作为 `session_id`。示例再派生两份运行信息：

```python
session_id = str(uuid4())
```

```python
def build_config(session_id: str, handler: CallbackHandler) -> RunnableConfig:
    return {
        "callbacks": [handler],
        "configurable": {
            "thread_id": f"thread-{session_id}",
        },
        "metadata": {
            "example": "20_langgraph_deepagents_langfuse",
            "langfuse_session_id": session_id,
            "langfuse_tags": ["deepagents-cookbook", "langgraph-deepagents"],
        },
        "run_name": "langgraph_deepagents_langfuse_demo",
    }
```

`langfuse_session_id` 是 Langfuse LangChain callback 识别的字段。它会写到 trace 的 `sessionId` 上。

`thread_id` 放在 `configurable` 里。外层 LangGraph 或内层 DeepAgents 如果接了 checkpointer，就会用它恢复运行现场。

## 运行方式

先确认 `.env` 里有模型变量和 Langfuse 变量：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash

LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxx
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

如果使用 Langfuse US 区域，`LANGFUSE_BASE_URL` 改成：

```bash
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

运行示例：

```bash
uv run --env-file .env python examples/20_langgraph_deepagents_langfuse/langgraph_deepagents_langfuse.py
```

示例输出类似：

```text
sessionId: 3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6
threadId: thread-3d0f7e77-1fd5-45a2-9623-e1c7d2fc7bb6
traceId: 8a7f0b91-2c8e-4d5a-8f16-0e9c2b4d6a71
answer: 订单 A1003 已取消，退款处理中。需要人工处理。
needsReview: True
```

打开 Langfuse 项目后，在 Traces 里可以看到外层 LangGraph 节点和内层 DeepAgents 运行。到 Sessions 里按 `sessionId` 查，也能看到这次 trace。

## 关键点

- `CallbackHandler` 挂在外层 `graph.invoke(..., config=...)`。
- DeepAgents 节点必须接收 `config: RunnableConfig`，并传给 `order_agent.invoke(...)`。
- 示例每次运行生成新的 `session_id`。真实服务可以在请求入口生成，也可以从业务会话里读取。
- 服务边界负责派生 `thread_id` 和 `langfuse_session_id`。
- `session_id` 管观测聚合。`thread_id` 管 LangGraph 运行现场。它们可以来自同一个业务会话，但不是同一个概念。
- 短脚本退出前调用 `langfuse.flush()`，避免 trace 还没发送完进程就结束。

## 取舍

这个示例不加 FastAPI，也不接外部 checkpointer。它只演示外层 LangGraph 调内层 DeepAgents 时，怎么无侵入式接入 Langfuse。

生产环境里，`session_id` 通常来自 HTTP header、登录会话或任务表。不要把密钥、完整手机号、身份证号或敏感订单明细放进去。
