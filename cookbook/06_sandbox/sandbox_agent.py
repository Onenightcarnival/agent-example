"""Run an agent with a filesystem backend and write limits."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        workspace = root / "workspace"
        workspace.mkdir()
        (workspace / "input.md").write_text(
            "# 待整理\n\n- model：判断下一步\n- tool：操作外部系统\n",
            encoding="utf-8",
        )

        model = ChatOpenAI(
            model=os.environ["MODEL_NAME"],
            api_key=os.environ["MODEL_API_KEY"],
            base_url=os.environ.get("MODEL_BASE_URL") or None,
        )

        agent = create_deep_agent(
            model=model,
            system_prompt=(
                "你是文档整理助手。读取 /workspace/input.md，把内容整理成两段短说明，写入 /workspace/output.md。"
            ),
            backend=FilesystemBackend(root_dir=root, virtual_mode=True),
            permissions=[
                FilesystemPermission(
                    operations=["write"],
                    paths=["/workspace/**"],
                    mode="allow",
                ),
                FilesystemPermission(
                    operations=["write"],
                    paths=["/**"],
                    mode="deny",
                ),
            ],
        )

        agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "请整理输入文件，并写入输出文件。",
                    }
                ]
            }
        )

        print((workspace / "output.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
