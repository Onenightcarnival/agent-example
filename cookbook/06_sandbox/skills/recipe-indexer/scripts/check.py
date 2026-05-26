"""Run a cheap self-check for the recipe-indexer skill."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_recipe_index import build_index, parse_items


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        input_path = root / "recipe_notes.md"
        output_path = root / "recipe_index.md"
        input_path.write_text(
            "\n".join(
                [
                    "# recipe notes",
                    "",
                    "- 01_model：接入模型",
                    "- 02_tools_mcp: 接入 MCP tool",
                ]
            ),
            encoding="utf-8",
        )

        items = parse_items(input_path.read_text(encoding="utf-8"))
        output_path.write_text(build_index(items), encoding="utf-8")
        output = output_path.read_text(encoding="utf-8")

    if "`01_model`：接入模型" not in output:
        raise SystemExit("missing 01_model entry")
    if "`02_tools_mcp`：接入 MCP tool" not in output:
        raise SystemExit("missing 02_tools_mcp entry")
    if "共 2 个 recipe。" not in output:
        raise SystemExit("wrong recipe count")

    print("recipe-indexer check passed")


if __name__ == "__main__":
    main()
