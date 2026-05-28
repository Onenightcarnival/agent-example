# 06 sandbox

## 场景

agent 要完成工作，不能只靠模型和对话。它需要一台能放文件、跑命令、保留中间结果的机器。

这里把带持久化卷的 AIO Sandbox 当成 agent 的工作电脑。文件、缓存、配置、半成品工程，都在这台机器上。

换一份任务可以换目录，甚至换一台 sandbox。但一台长期使用的 sandbox，本身就是稳定的工作环境。

这一章不讲本地 `FilesystemBackend`。它讲另一种接法：通过 MCP 连接远程 sandbox，让 agent 用 MCP tools 操作文件和终端。

示例会做三件事：

- 初始化 agent 前，把一个带 `scripts/` 的 Python skill 写入 sandbox 的持久化目录。
- 初始化 agent 时，把 skill 路径、输入路径和输出路径放进 system prompt。
- 用户只说一句话：请使用这个 skill 帮我做事。

示例里的用户输入是：

```text
请使用 example-indexer skill 帮我整理 example notes。
```

agent 会读取 sandbox 里的 `SKILL.md`，再通过 `sandbox_execute_bash` 运行 skill 自带脚本，并读取输出文件。

示例还挂了一个 callback。运行时会打印每次 tool call 的输入和输出，用来确认结果来自 sandbox，而不是模型自己猜的。

## 代码

见 [sandbox_agent.py](sandbox_agent.py)。

demo skill 放在 [skills/example-indexer/SKILL.md](skills/example-indexer/SKILL.md)。它的脚本是 [skills/example-indexer/scripts/build_example_index.py](skills/example-indexer/scripts/build_example_index.py)。

这个 skill 很小。它读取一份 example notes，生成 Markdown 索引。重点不是索引本身，而是演示 skill 可以带脚本，脚本在远程 sandbox 里执行。

## 运行方式

先启动 AIO Sandbox，并给它挂一个持久化卷。下面只是示例命令，目录可以换成你自己的路径：

```bash
docker run --security-opt seccomp=unconfined \
  --rm -it \
  -p 8080:8080 \
  -v "$PWD/.sandbox-workspace:/home/gem/workspace" \
  ghcr.io/agent-infra/sandbox:latest
```

示例默认连接：

```bash
http://localhost:8080/mcp
```

如果端口或路径不同，在 `.env` 里设置：

```bash
SANDBOX_MCP_SERVER_URL=http://localhost:8080/mcp
```

如果 sandbox MCP server 需要鉴权，也在 `.env` 里设置 auth：

```bash
SANDBOX_MCP_AUTH_HEADER="Authorization: Bearer xxxx"
```

代码会把这个值作为 MCP 请求的 header。

模型环境变量沿用第一章：

```bash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=xxxx
MODEL_NAME=deepseek-v4-pro
```

运行：

```bash
uv run --env-file .env python examples/06_sandbox/sandbox_agent.py
```

运行后，sandbox 的持久化卷里会出现这些文件：

```text
/home/gem/workspace/deepagents-examples/
  skills/example-indexer/SKILL.md
  skills/example-indexer/pyproject.toml
  skills/example-indexer/scripts/build_example_index.py
  skills/example-indexer/scripts/check.py
  skills/example-indexer/tests/test_build_example_index.py
  skills/example-indexer/uv.lock
  input/example_notes.md
  output/example_index.md
```

## 关键点

- sandbox 不是一次性临时目录。它更像 agent 的远程工作电脑。
- MCP 是 agent 连接这台电脑的方式。
- AIO Sandbox 的 `/mcp` 端点会暴露文件、终端、浏览器等 tools。
- 这个示例主要用 `sandbox_file_operations` 和 `sandbox_execute_bash`。
- skill 的 `SKILL.md` 负责告诉 agent 什么时候用、怎么用。
- skill 的 `scripts/` 负责放稳定、可重复的 Python 逻辑。
- `pyproject.toml` 和 `uv.lock` 负责固定 Python 运行环境。
- `scripts/check.py` 和 `tests/` 负责给脚本做最小验证。
- 脚本在 sandbox 里执行，依赖、缓存和输出也留在 sandbox。
- `PrintToolCalls` callback 会打印模型触发的 tool 输入和输出。
- `DisableBuiltinTools` 会过滤 DeepAgents 内置工具，避免示例误用本地文件或命令工具。

## 取舍

远程 sandbox 适合让 agent 做带执行步骤的工作，比如跑脚本、处理文件、安装依赖、维护半成品工程。

它也适合执行带 `scripts/` 的 skill，因为脚本需要真实文件系统和命令行。

sandbox 不等于放开权限。能只给工作目录，就不要给整台机器。能让脚本写固定输出路径，就不要让它随便写。涉及删除、发布、外部写入或密钥访问时，仍要加确认步骤。
