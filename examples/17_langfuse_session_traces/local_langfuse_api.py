"""Call the local Langfuse Public API and print raw JSON."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from typing import Any

import httpx
import langfuse_session_traces as demo


def api_base_url() -> str:
    return os.environ.get("LANGFUSE_LOCAL_BASE_URL") or os.environ["LANGFUSE_BASE_URL"]


def api_client() -> httpx.Client:
    return httpx.Client(
        base_url=api_base_url().rstrip("/"),
        auth=(os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"]),
        timeout=30,
        trust_env=False,
    )


def print_json(title: str, response: httpx.Response) -> None:
    print(f"\n{title}")
    print(f"GET {response.request.url}")
    print(f"status: {response.status_code}")
    try:
        payload: Any = response.json()
    except json.JSONDecodeError:
        print(response.text)
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_payload(title: str, payload: Any) -> None:
    print(f"\n{title}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def wait_for_traces(client: httpx.Client, trace_ids: list[str], timeout_seconds: int = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    missing = set(trace_ids)

    while missing and time.monotonic() < deadline:
        for trace_id in list(missing):
            response = client.get(f"/api/public/traces/{trace_id}")
            if response.status_code == 200:
                missing.remove(trace_id)
        if missing:
            time.sleep(2)

    if missing:
        print(f"public api 还没返回这些 trace：{', '.join(sorted(missing))}")


def main() -> None:
    langfuse = demo.build_langfuse()
    agent = demo.build_agent()
    from_timestamp = datetime.now(UTC)
    messages = [
        "查一下订单 A1002 的状态，并用一句话回复。",
        "查一下订单 A1003 的状态，并用一句话回复。",
        "查一下订单 A1001 的状态，并用一句话回复。",
    ]

    print(f"local langfuse api: {api_base_url().rstrip('/')}")
    print(f"sessionId: {demo.SESSION_ID}")

    turns: list[demo.TurnResult] = []
    for index, message in enumerate(messages, start=1):
        turn = demo.run_turn(agent, index, message)
        turns.append(turn)
        print(f"turn {turn.index}: traceId={turn.trace_id}, langfuseTraceId={turn.langfuse_trace_id}")

    langfuse.flush()
    to_timestamp = datetime.now(UTC)

    with api_client() as client:
        wait_for_traces(client, [turn.langfuse_trace_id for turn in turns])

        traces_response = client.get(
            "/api/public/traces",
            params={
                "page": 1,
                "limit": 100,
                "fromTimestamp": from_timestamp.isoformat(),
                "toTimestamp": to_timestamp.isoformat(),
            },
        )
        print_json("traces by time range", traces_response)
        if traces_response.status_code == 200:
            trace_ids = {turn.langfuse_trace_id for turn in turns}
            payload = traces_response.json()
            matched = [trace for trace in payload.get("data", []) if trace.get("id") in trace_ids]
            print_payload("matched traces from response", matched)

        for turn in turns:
            observations_response = client.get(
                "/api/public/v2/observations",
                params={
                    "traceId": turn.langfuse_trace_id,
                    "limit": 100,
                },
            )
            print_json(f"observations for turn {turn.index}", observations_response)


if __name__ == "__main__":
    main()
