# 14 dynamic tool headers

## 场景

agent 包成服务以后，tool 调用常常要带上动态 header。

一种动态 header 来自用户请求。比如用户访问业务系统时带了 `Authorization` 或 `Cookie`。agent 服务不能让模型自己填写这些值。服务应该从 HTTP 请求里读取这些 header，再转发给 MCP server。MCP server 用它判断当前用户能访问哪些数据。

另一种动态 header 来自服务端。比如 agent 服务自己持有一个静态 token，请求开始时先调用内部函数换一个短期 token，再把短期 token 传给 MCP server。静态 token 不进入模型，也不传给 MCP tool。

这个示例演示两类动态 header：

- `service_app.py` 暴露 `/chat`。
- 服务只从用户请求转发 `Authorization`、`Cookie` 和 `X-Tenant-Id`。
- 服务用 `PROFILE_STATIC_TOKEN` 换出短期 token，再写入 `X-Service-Authorization`。
- MCP tool 根据请求 header 返回当前用户资料。
- 模型只能调用 `get_current_user_profile`，看不到真实 token、cookie 和服务端静态 token。

## 代码

见 [service_app.py](service_app.py) 和 [mock_mcp_server.py](mock_mcp_server.py)。

`service_app.py` 每次请求都会用当前 header 创建 MCP tools。
用户身份来自请求 header：

```python
headers = {**user_headers(authorization, cookie, x_tenant_id), **service_headers()}
tools = await load_profile_tools(headers)
agent = build_agent(tools)
```

服务端短期 token 来自静态 token 交换：

```python
def service_headers() -> dict[str, str]:
    static_token = os.environ.get("PROFILE_STATIC_TOKEN")
    if not static_token:
        return {}
    dynamic_token = exchange_service_token(static_token)
    return {"X-Service-Authorization": f"Bearer {dynamic_token}"}
```

`mock_mcp_server.py` 的 tool 不接收 token 参数。它从 MCP 请求 header 里识别用户：

```python
@mcp.tool()
async def get_current_user_profile(ctx: Context) -> dict[str, str]:
    tenant_id = header_value(ctx, "x-tenant-id") or "default"
    user_id = user_from_headers(ctx)
    ...
```

## 运行方式

先确认 `.env` 里有模型变量：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-flash
PROFILE_STATIC_TOKEN=static-profile-secret
```

启动 mock MCP server：

```bash
uv run --env-file .env python examples/14_dynamic_tool_headers/mock_mcp_server.py
```

另开一个终端，启动 agent 服务：

```bash
uv run --env-file .env uvicorn examples.14_dynamic_tool_headers.service_app:app --reload --port 8015
```

调用服务，并传入请求级身份：

```bash
curl -X POST http://127.0.0.1:8015/chat \
  -H 'content-type: application/json' \
  -H 'authorization: Bearer token-alice' \
  -H 'cookie: session=alice' \
  -H 'x-tenant-id: acme' \
  -H 'x-thread-id: profile-thread-001' \
  -d '{"message":"查一下我当前用户资料，用一句话回答。"}'
```

返回示例：

```json
{
  "answer": "你当前是 Alice Chen，属于 acme 租户，套餐是 team。",
  "thread_id": "profile-thread-001",
  "forwarded_headers": ["Authorization", "Cookie", "X-Tenant-Id", "X-Service-Authorization"]
}
```

换成另一个 token：

```bash
curl -X POST http://127.0.0.1:8015/chat \
  -H 'content-type: application/json' \
  -H 'authorization: Bearer token-bob' \
  -H 'x-tenant-id: acme' \
  -d '{"message":"查一下我当前用户资料，用一句话回答。"}'
```

这次 MCP server 会看到 `Bearer token-bob`，并返回 Bob 的资料。

如果设置了 `PROFILE_STATIC_TOKEN=static-profile-secret`，服务还会先换出 `Bearer dynamic-profile-token`，再把它放进 `X-Service-Authorization` 发给 MCP server。这个值不会出现在 prompt 或响应正文里。响应里的 `forwarded_headers` 只列出 header 名，方便确认本次转发了哪些字段。

如果 mock MCP server 地址不同，在 `.env` 里设置：

```bash
PROFILE_MCP_SERVER_URL=http://127.0.0.1:8014/mcp
```

## 关键点

- 动态 header 是请求级上下文。不要放进全局缓存的 MCP client。
- 服务层决定转发哪些用户 header。示例只从请求里转发 `Authorization`、`Cookie` 和 `X-Tenant-Id`。
- 服务端静态 token 只用于换短期 token。不要直接传给 MCP server。
- 用户 token、cookie、服务端静态 token 和短期 token 都不应该进入 prompt、`state`、trace metadata 或普通日志。
- `get_current_user_profile` 不暴露 `token` 参数。模型不能自己编一个 token 来调用 tool。
- `MultiServerMCPClient` 的 `headers` 会用于 MCP 请求。这个示例每次请求创建带当前 header 的 tools。
- 如果 MCP server 会按用户身份裁剪 tool 列表，加载 tools 这一步也应该使用同一组 header。

## 取舍

这个示例为了讲清楚动态 header，每次请求都会创建 MCP client、加载 tools，再创建 agent。这样最直观，但不是吞吐量最高的做法。

生产环境通常会把模型、静态配置和安全策略缓存起来。请求级身份仍然要单独处理。可以封装一个 factory，只在请求开始时生成带当前 header 的 MCP tools。

这里没有加入鉴权、CSRF、防重放、审计和脱敏日志。真实服务应该先验证调用方身份，再决定是否把 header 转发给下游 MCP server。
