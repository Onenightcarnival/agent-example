"""Build a small Markdown index from cookbook recipe notes."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ITEM_PATTERN = re.compile(r"^-\s*(?P<chapter>\d{2}_[a-z0-9_]+)\s*[：:]\s*(?P<summary>.+?)\s*$")


def parse_items(text: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = ITEM_PATTERN.match(line)
        if match:
            items.append((match.group("chapter"), match.group("summary")))
    return items


def build_index(items: list[tuple[str, str]]) -> str:
    lines = ["# Recipe index", ""]
    if not items:
        lines.append("暂无 recipe 条目。")
    else:
        for chapter, summary in items:
            lines.append(f"- `{chapter}`：{summary}")
    lines.extend(["", f"共 {len(items)} 个 recipe。", ""])
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_recipe_index.py <input.md> <output.md>")

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    items = parse_items(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_index(items), encoding="utf-8")


if __name__ == "__main__":
    main()
