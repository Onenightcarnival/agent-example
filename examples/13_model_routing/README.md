# 13 model_routing

agent 进入生产环境后，不一定每次都要用同一个模型。

简单问答、短摘要和小改写可以交给便宜、响应快的模型。多步骤推理、代码方案、风险判断和长上下文整理更适合交给能力更强的模型。

这个示例演示一个最小路由：

- 默认 worker model 是 `MODEL_SIMPLE_NAME`
- simple model 先做一次结构化判断，输出 `simple` 或 `complex`
- DeepAgents 的 middleware 在模型调用前替换本次使用的 model
- 路由结果写进 `context`，同一次运行里后续模型调用复用这个结果

## 代码

见 [model_routing.py](model_routing.py)。

核心逻辑在 `SimpleComplexRouter.wrap_model_call(...)`。

```python
decision = self.route_once(request.runtime.context, latest_user_text(request.messages))
model = self.complex_model if decision.route == "complex" else self.simple_model
return handler(request.override(model=model, tools=tools))
```

`route_once(...)` 使用 `flash` 做一次普通模型调用，再用 `PydanticOutputParser` 校验输出。
这样不依赖 MaaS 是否支持 OpenAI 的 `response_format` 参数。

路由结果只有两类：

```python
class RouteDecision(BaseModel):
    route: Literal["simple", "complex"]
    reason: str
```

## 运行方式

先配置基础模型。

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash
MODEL_TIMEOUT_SECONDS=30
```

不填写时，示例默认使用 `deepseek-v4-flash` 和 `deepseek-v4-pro`。
也可以显式指定模型名。这里的值可以换成你的 MaaS 模型名：

```bash
MODEL_SIMPLE_NAME=deepseek-v4-flash
MODEL_COMPLEX_NAME=deepseek-v4-pro
```

为了兼容旧变量，示例也会读取 `MODEL_FLASH_NAME` 和 `MODEL_PRO_NAME`。

运行示例：

```bash
uv run --env-file .env python examples/13_model_routing/model_routing.py
```

示例会跑两条请求，并打印路由结果：

```text
user: 我刚接触 DeepAgents，用两句话解释 model 在 agent 里负责什么。
route: simple (...)
router_model: deepseek-v4-flash
worker_model: deepseek-v4-flash
assistant: ...
elapsed: ...

user: 我们现在所有请求都用 deepseek-v4-flash。请设计一个最小改造方案...
route: complex (...)
router_model: deepseek-v4-flash
worker_model: deepseek-v4-pro
assistant: ...
elapsed: ...
```

## 关键点

- `create_deep_agent(model=simple_model, ...)` 只设置默认模型。
- `request.override(model=...)` 决定这一次模型调用实际使用哪个模型。
- `context` 适合保存本次运行的路由结果，避免每一轮模型调用都重新判断。
- 路由模型使用 simple model。它只做分类，不负责完成业务任务。
- `RouteDecision` 只保留 `simple` 和 `complex` 两个路由键，真实 model name 放在环境变量里。
- `MODEL_TIMEOUT_SECONDS` 用来避免 MaaS 或某个模型长时间不返回。
- 这个示例继续过滤 DeepAgents 内置工具，便于观察模型路由本身。

## 取舍

这个做法适合最小化接入。它只有两个档位，也没有外部策略服务。

生产环境可以继续补这些内容：

- 增加确定性规则，比如用户等级、预算、上下文长度和失败次数。
- 把路由结果写进 trace，方便看成本和误判。
- 对高风险 tool 单独升级到 `pro`，不要只看任务难度。
- 在 MaaS 层做容灾和供应商切换，应用层仍然负责业务判断。
