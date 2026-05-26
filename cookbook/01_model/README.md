# 01 model

## 场景

先把模型接入 agent。

这个示例使用 OpenAI 兼容接口初始化 `ChatOpenAI`，再把它传给 `create_deep_agent`。示例会关闭 DeepSeek thinking、传入自定义 `httpx.Client`，并过滤 DeepAgents 内置工具。

## 代码

见 [model_connection.py](model_connection.py)。

## 运行方式

先在 `.env` 里设置模型接入参数。

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-pro
```

运行：

```bash
uv run --env-file .env python cookbook/01_model/model_connection.py
```

## 关键点

- `MODEL_NAME` 对应具体模型名，比如 `deepseek-v4-pro`。
- `MODEL_API_KEY` 是模型服务的密钥。
- `MODEL_BASE_URL` 指向 OpenAI 兼容接口。使用 OpenAI 官方接口时可以不设置。
- `extra_body={"thinking": {"type": "disabled"}}` 关闭 DeepSeek thinking。
- `httpx.Client(trust_env=False)` 忽略本机代理等环境变量。
- `DisableBuiltinTools` 会在模型调用前过滤 DeepAgents 内置工具。
- `model` 可以传 `provider:model` 字符串，也可以传已经初始化好的 chat model。
- `system_prompt` 会影响模型回答。这里只放一条很短的角色说明。

## 取舍

这个 recipe 只检查模型接入。tool、多轮对话、memory 和文件读写放到后面的章节。
