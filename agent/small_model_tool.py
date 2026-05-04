"""Small model invoked as a tool: constrained prompts, JSON-only outputs."""

from __future__ import annotations

import json
import re
import time
from typing import Any

from openai import OpenAI

OPERATIONS = frozenset(
    {
        "summarise_large",
        "extract_relevant",
        "triage_tests",
        "classify_diff",
        "dependency_scan",
        "summarise_stacktrace",
    }
)

_SYSTEM_BY_OP: dict[str, str] = {
    "summarise_large": (
        "You compress source files or logs. Reply with ONE JSON object only, no markdown. "
        'Schema: {"summary": string, "key_symbols": string[], "risks": string[]}'
    ),
    "extract_relevant": (
        "You find minimal evidence for a query in the given content. "
        "Reply with ONE JSON object only. "
        'Schema: {"matches": [{"line_hint": string, "snippet": string}], "notes": string}'
    ),
    "triage_tests": (
        "You triage pytest/unittest style output. Reply with ONE JSON object only. "
        'Schema: {"root_cause": string, "locations": string[], "next_action": string}'
    ),
    "classify_diff": (
        "You judge if a diff is safe to apply. Reply with ONE JSON object only. "
        'Schema: {"safe": boolean, "reason": string, "watchouts": string[]}'
    ),
    "dependency_scan": (
        "You list likely callers / references from the provided excerpts. "
        "Reply with ONE JSON object only. "
        'Schema: {"references": [{"file": string, "line": number, "snippet": string}]}'
    ),
    "summarise_stacktrace": (
        "You summarise a Python stack trace. Reply with ONE JSON object only. "
        'Schema: {"error_type": string, "failing_frame": string, "likely_cause": string}'
    ),
}


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if m:
        text = m.group(0)
    return json.loads(text)


def run_small_model_operation(
    *,
    client: OpenAI,
    model: str,
    operation: str,
    payload: dict[str, Any],
    max_tokens_out: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Returns (structured_result, usage_meta) where usage_meta has input_tokens, output_tokens, wall_time_s.
    """
    if operation not in OPERATIONS:
        return (
            {"ok": False, "error": "unknown_operation", "allowed": sorted(OPERATIONS)},
            {"input_tokens": 0, "output_tokens": 0, "wall_time_s": 0.0},
        )

    content = str(payload.get("content", ""))
    query = str(payload.get("query", ""))
    cap = int(payload.get("max_tokens_out") or max_tokens_out or 400)
    cap = max(64, min(cap, 800))

    user = json.dumps(
        {"operation": operation, "query": query, "content": content},
        ensure_ascii=False,
    )

    system = _SYSTEM_BY_OP[operation]
    t0 = time.perf_counter()
    kwargs: dict[str, Any] = dict(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.1,
        max_tokens=cap,
    )
    try:
        resp = client.chat.completions.create(
            **kwargs, response_format={"type": "json_object"}
        )
    except Exception:
        resp = client.chat.completions.create(**kwargs)
    wall = time.perf_counter() - t0
    msg = resp.choices[0].message.content or "{}"
    usage = getattr(resp, "usage", None) or None
    inp = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
    out = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0

    try:
        parsed = _extract_json_object(msg)
    except json.JSONDecodeError:
        parsed = {"ok": False, "error": "json_parse_failed", "raw": msg[:2000]}

    meta = {"input_tokens": inp, "output_tokens": out, "wall_time_s": wall}
    if isinstance(parsed, dict):
        parsed = {"ok": True, **parsed}
    else:
        parsed = {"ok": False, "error": "unexpected_shape", "raw": parsed}
    return parsed, meta
