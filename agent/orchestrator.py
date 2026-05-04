"""Large-model ReAct loop with tool dispatch and usage logging."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from openai import NotFoundError, OpenAI

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import Settings, get_settings
from eval.metrics import MetricsSession

from .tools import ToolContext, dispatch_tool, parse_tool_calls, tool_schemas


def _system_prompt(*, dual_model: bool) -> str:
    base = (
        "You are a senior software engineer agent. You work inside a single workspace root. "
        "Use tools to read, search, edit, and run tests. Prefer minimal, correct changes. "
        "When you are done, call finish with success=true only if verification passed.\n\n"
    )
    if dual_model:
        return (
            base
            + "Context discipline: never pull huge raw sources into your reasoning via read_file. "
            + "If read_file returns file_too_large_for_direct_read, use small_model_tool with "
            + "payload.path pointing at the same file and a precise query. "
            + "For long command output (tests, traces), pass the raw text as payload.content to "
            + "small_model_tool (triage_tests or summarise_stacktrace) and act on the structured JSON.\n"
        )
    return (
        base
        + "You may read full files directly with read_file when helpful; there is no small-model delegate.\n"
    )


def _assistant_message_dict(msg: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"role": "assistant", "content": msg.content}
    tcs = getattr(msg, "tool_calls", None)
    if tcs:
        out["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments or "{}",
                },
            }
            for tc in tcs
        ]
    return out


def run_react_loop(
    *,
    workspace_root: Path,
    task_user_message: str,
    settings: Settings | None = None,
    dual_model: bool = True,
    metrics: MetricsSession | None = None,
) -> dict[str, Any]:
    """
    Runs until finish tool, max steps, or empty tool resolution.
    Returns dict with final message, success, messages, metrics summary.
    """
    settings = settings or get_settings()
    metrics = metrics or MetricsSession(settings=settings)

    client = OpenAI(
        base_url=settings.nvidia_base_url,
        api_key=settings.nvidia_api_key,
    )

    def on_api_usage(meta: dict[str, Any]) -> None:
        role = meta.get("role", "unknown")
        metrics.log_call(
            model=str(meta.get("model", "")),
            role=str(role),
            operation=str(meta.get("operation", "")),
            input_tokens=int(meta.get("input_tokens", 0)),
            output_tokens=int(meta.get("output_tokens", 0)),
            wall_time_s=float(meta.get("wall_time_s", 0.0)),
        )

    ctx = ToolContext(
        workspace_root=workspace_root.resolve(),
        client=client,
        large_model=settings.large_model,
        small_model=settings.small_model,
        dual_model=dual_model,
        read_file_max_lines_dual=settings.read_file_max_lines_dual,
        on_api_usage=on_api_usage,
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _system_prompt(dual_model=dual_model)},
        {"role": "user", "content": task_user_message},
    ]

    final_message = ""
    success = False

    for _ in range(settings.max_orchestrator_steps):
        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(
                model=settings.large_model,
                messages=messages,
                tools=tool_schemas(dual_model=dual_model),
                tool_choice="auto",
                temperature=0.2,
            )
        except NotFoundError as e:
            raise RuntimeError(
                f"Chat completions returned 404 for model {settings.large_model!r}. "
                "On build.nvidia.com, open a model you have access to, copy the exact "
                "`model` string from the OpenAI example, and set LARGE_MODEL in .env. "
                "Slugs like nvidia/llama-3.1-nemotron-70b-instruct can map to a function "
                "your key is not entitled to (API error mentions Function '…' not found). "
                f"Original: {e}"
            ) from e
        wall = time.perf_counter() - t0
        msg = resp.choices[0].message
        usage = getattr(resp, "usage", None)
        inp = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
        out = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0
        on_api_usage(
            {
                "role": "large",
                "model": settings.large_model,
                "operation": "orchestrator.chat",
                "input_tokens": inp,
                "output_tokens": out,
                "wall_time_s": wall,
            }
        )
        metrics.bump_step()

        messages.append(_assistant_message_dict(msg))

        calls = parse_tool_calls(msg)
        if not calls:
            final_message = (msg.content or "").strip()
            break

        finish_payload: dict[str, Any] | None = None
        for tc in calls:
            result = dispatch_tool(tc["name"], tc["arguments"], ctx)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
            if tc["name"] == "finish" and result.get("finished"):
                finish_payload = result
        if finish_payload is not None:
            return {
                "success": bool(finish_payload.get("success")),
                "final_message": str(finish_payload.get("message", "")),
                "messages": messages,
                "metrics": metrics.summary_dict(),
            }

    return {
        "success": success,
        "final_message": final_message or "stopped: max steps or no finish tool",
        "messages": messages,
        "metrics": metrics.summary_dict(),
    }
