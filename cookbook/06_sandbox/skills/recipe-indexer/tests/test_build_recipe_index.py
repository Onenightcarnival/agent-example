from scripts.build_recipe_index import build_index, parse_items


def test_parse_items_accepts_chinese_and_ascii_colons() -> None:
    text = "\n".join(
        [
            "- 01_model：接入模型",
            "- 02_tools_mcp: 接入 MCP tool",
            "- not_a_recipe：忽略这一行",
        ]
    )

    assert parse_items(text) == [
        ("01_model", "接入模型"),
        ("02_tools_mcp", "接入 MCP tool"),
    ]


def test_build_index_writes_empty_state() -> None:
    assert build_index([]) == "# Recipe index\n\n暂无 recipe 条目。\n\n共 0 个 recipe。\n"
