"""Mock MCP server that reads identity from request headers."""

from __future__ import annotations

import os

from mcp.server.fastmcp import Context, FastMCP


def build_server() -> FastMCP:
    return FastMCP(
        "Profile MCP",
        host=os.environ.get("PROFILE_MCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("PROFILE_MCP_PORT", "8014")),
        streamable_http_path="/mcp",
        stateless_http=True,
    )


mcp = build_server()


def header_value(ctx: Context, name: str) -> str | None:
    request = ctx.request_context.request
    if request is None:
        return None
    return request.headers.get(name)


def user_from_headers(ctx: Context) -> str:
    authorization = header_value(ctx, "authorization")
    cookie = header_value(ctx, "cookie")

    if authorization == "Bearer token-alice":
        return "alice"
    if authorization == "Bearer token-bob":
        return "bob"
    if cookie and "session=alice" in cookie:
        return "alice"
    if cookie and "session=bob" in cookie:
        return "bob"
    return "anonymous"


def service_token_status(ctx: Context) -> str:
    service_authorization = header_value(ctx, "x-service-authorization")
    if service_authorization == "Bearer dynamic-profile-token":
        return "ok"
    if service_authorization and service_authorization.startswith("Bearer dynamic-"):
        return "ok"
    return "missing"


@mcp.tool()
async def get_current_user_profile(ctx: Context) -> dict[str, str]:
    """Return the current user's profile from request headers."""
    tenant_id = header_value(ctx, "x-tenant-id") or "default"
    user_id = user_from_headers(ctx)
    profiles = {
        ("alice", "acme"): {
            "user_id": "alice",
            "tenant_id": "acme",
            "display_name": "Alice Chen",
            "plan": "team",
        },
        ("bob", "acme"): {
            "user_id": "bob",
            "tenant_id": "acme",
            "display_name": "Bob Lin",
            "plan": "free",
        },
    }
    profile = profiles.get(
        (user_id, tenant_id),
        {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "display_name": "Guest",
            "plan": "unknown",
        },
    )
    profile["service_token_status"] = service_token_status(ctx)
    return profile


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
