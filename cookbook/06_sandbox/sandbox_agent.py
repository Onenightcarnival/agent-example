"""Run a script-backed skill inside an AIO Sandbox through MCP."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

import httpx
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

SANDBOX_WORKSPACE = "/home/gem/workspace/deepagents-cookbook"
SKILL_NAME = "recipe-indexer"
IGNORED_SKILL_PARTS = frozenset(
    {
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
    }
)

BUILTIN_TOOLS = frozenset(
    {
        "write_todos",
        "ls",
        "read_file",
        "write_file",
        "edit_file",
        "glob",
        "grep",
        "execute",
        "task",
    }
)


@dataclass(frozen=True)
class SandboxPaths:
    skill_path: str
    skill_root: str
    input_path: str
    output_path: str


def tool_name(tool) -> str | None:
    if isinstance(tool, dict):
        name = tool.get("name")
        return name if isinstance(name, str) else None
    name = getattr(tool, "name", None)
    return name if isinstance(name, str) else None


class DisableBuiltinTools(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        tools = [tool for tool in request.tools if tool_name(tool) not in BUILTIN_TOOLS]
        return handler(request.override(tools=tools))

    async def awrap_model_call(self, request, handler):
        tools = [tool for tool in request.tools if tool_name(tool) not in BUILTIN_TOOLS]
        return await handler(request.override(tools=tools))


def format_payload(value: Any, *, max_length: int = 2000) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n... <truncated>"


def clean_tool_inputs(inputs: dict[str, Any] | None, input_str: str) -> Any:
    if inputs is None:
        return input_str
    return {key: value for key, value in inputs.items() if key != "runtime"}


def clean_tool_output(output: Any) -> Any:
    content = getattr(output, "content", None)
    return content if content is not None else output


class PrintToolCalls(AsyncCallbackHandler):
    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        tool = serialized.get("name") or serialized.get("id") or "unknown_tool"
        print(f"\n[tool:start] {tool}")
        print(format_payload(clean_tool_inputs(inputs, input_str)))

    async def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        print("[tool:end]")
        print(format_payload(clean_tool_output(output)))

    async def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        print("[tool:error]")
        print(str(error))


def mcp_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=headers, timeout=timeout, auth=auth, trust_env=False)


async def load_sandbox_tools():
    client = MultiServerMCPClient(
        {
            "sandbox": {
                "transport": "streamable_http",
                "url": os.environ.get("SANDBOX_MCP_SERVER_URL", "http://localhost:8080/mcp"),
                "timeout": timedelta(seconds=30),
                "sse_read_timeout": timedelta(seconds=300),
                "httpx_client_factory": mcp_http_client,
            }
        }
    )
    return await client.get_tools()


def find_tool(tools, name: str):
    for tool in tools:
        if tool_name(tool) == name:
            return tool
    available = ", ".join(sorted(filter(None, (tool_name(tool) for tool in tools))))
    msg = f"没有找到 MCP tool：{name}。当前 tools：{available}"
    raise RuntimeError(msg)


async def write_sandbox_file(file_write, path: str, content: str) -> None:
    await file_write.ainvoke({"action": "write", "path": path, "content": content})


async def write_skill_directory(file_write, terminal_execute, source_dir: Path, target_dir: str) -> None:
    source_files = sorted(
        path for path in source_dir.rglob("*") if path.is_file() and not IGNORED_SKILL_PARTS.intersection(path.parts)
    )
    directories = sorted(
        {
            target_dir,
            *(f"{target_dir}/{path.relative_to(source_dir).parent.as_posix()}" for path in source_files),
        }
    )
    await terminal_execute.ainvoke({"cmd": "mkdir -p " + " ".join(directories)})

    for path in source_files:
        target_path = f"{target_dir}/{path.relative_to(source_dir).as_posix()}"
        await write_sandbox_file(file_write, target_path, path.read_text(encoding="utf-8"))


async def prepare_sandbox(tools) -> SandboxPaths:
    root = Path(__file__).resolve().parent
    skill_dir = root / "skills" / SKILL_NAME
    skill_root = f"{SANDBOX_WORKSPACE}/skills/{SKILL_NAME}"
    input_path = f"{SANDBOX_WORKSPACE}/input/recipe_notes.md"
    output_path = f"{SANDBOX_WORKSPACE}/output/recipe_index.md"

    file_write = find_tool(tools, "sandbox_file_operations")
    terminal_execute = find_tool(tools, "sandbox_execute_bash")

    await terminal_execute.ainvoke({"cmd": f"mkdir -p {SANDBOX_WORKSPACE}/input {SANDBOX_WORKSPACE}/output"})
    await write_skill_directory(file_write, terminal_execute, skill_dir, skill_root)
    await write_sandbox_file(
        file_write,
        input_path,
        "\n".join(
            [
                "# recipe notes",
                "",
                "- 01_model：接入模型，确认配置可用",
                "- 02_tools_mcp：接入 Python tool 和 MCP tool",
                "- 05_skills：把稳定做法写进 skill",
                "- 06_sandbox：用远程 sandbox 运行脚本",
            ]
        ),
    )

    return SandboxPaths(
        skill_path=f"{skill_root}/SKILL.md",
        skill_root=skill_root,
        input_path=input_path,
        output_path=output_path,
    )


async def main() -> None:
    model = ChatOpenAI(
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ.get("MODEL_BASE_URL") or None,
        http_client=httpx.Client(trust_env=False),
        extra_body={"thinking": {"type": "disabled"}},
    )
    mcp_tools = await load_sandbox_tools()
    paths = await prepare_sandbox(mcp_tools)

    agent = create_deep_agent(
        model=model,
        tools=mcp_tools,
        system_prompt=(
            "你在 AIO Sandbox 里工作。sandbox 是你的工作电脑。"
            "文件、脚本和中间结果都放在这台机器的持久化目录里。"
            f"程序已经把 {SKILL_NAME} skill 上传到 sandbox：{paths.skill_path}。"
            f"待处理文件是：{paths.input_path}。输出文件写到：{paths.output_path}。"
            "用户要求使用这个 skill 时，先读取 SKILL.md，再按 skill 说明运行脚本。"
            "只使用 sandbox MCP tools 操作文件和终端，优先使用 sandbox_file_operations 和 sandbox_execute_bash。"
        ),
        middleware=[DisableBuiltinTools()],
    )

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请使用 recipe-indexer skill 帮我整理 recipe notes。",
                }
            ]
        },
        config={"callbacks": [PrintToolCalls()]},
    )

    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
