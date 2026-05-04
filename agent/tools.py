"""Tool definitions (OpenAI function schema) and dispatch."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from openai import OpenAI

from .file_tools import (
    apply_unified_diff,
    read_file,
    run_command,
    search_files,
    write_file,
)
from .small_model_tool import run_small_model_operation


ToolHandler = Callable[..., dict[str, Any]]


def _coerce_tool_payload(raw: Any) -> dict[str, Any]:
    """LLMs sometimes emit payload as a JSON string, wrong type, or omit it."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {"content": raw}
    return {}


@dataclass
class ToolContext:
    workspace_root: Path
    client: OpenAI
    large_model: str
    small_model: str
    dual_model: bool
    read_file_max_lines_dual: int
    on_api_usage: Callable[[dict[str, Any]], None] | None = None


def _tool_def(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


def tool_schemas(*, dual_model: bool) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = [
        _tool_def(
            "read_file",
            "Read a UTF-8 text file under the task workspace. In dual-model mode, avoid huge files; use small_model_tool instead for large bodies.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        ),
        _tool_def(
            "write_file",
            "Overwrite or create a file with full contents.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        ),
        _tool_def(
            "search_files",
            "Regex search across Python files.",
            {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "glob": {"type": "string", "default": "**/*.py"},
                    "max_matches": {"type": "integer", "default": 50},
                },
                "required": ["pattern"],
            },
        ),
        _tool_def(
            "run_command",
            "Run a shell command in the workspace (list argv preferred).",
            {
                "type": "object",
                "properties": {
                    "argv": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["argv"],
            },
        ),
        _tool_def(
            "apply_patch",
            "Apply a unified diff (git style). May fail if patch is unavailable.",
            {
                "type": "object",
                "properties": {"diff": {"type": "string"}},
                "required": ["diff"],
            },
        ),
        _tool_def(
            "finish",
            "Call when the task is done. Include final message and whether success criteria met.",
            {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "success": {"type": "boolean"},
                },
                "required": ["message", "success"],
            },
        ),
    ]
    if dual_model:
        tools.insert(
            -1,
            _tool_def(
                "small_model_tool",
                "Delegate bulky raw I/O to the small model. Always prefer this over read_file for large files, traces, or multi-file grep output.",
                {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": [
                                "summarise_large",
                                "extract_relevant",
                                "triage_tests",
                                "classify_diff",
                                "dependency_scan",
                                "summarise_stacktrace",
                            ],
                        },
                        "payload": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Workspace-relative file to load into the small model (omit if content is passed).",
                                },
                                "content": {"type": "string"},
                                "query": {"type": "string"},
                                "max_tokens_out": {"type": "integer"},
                            },
                            "required": [],
                        },
                    },
                    "required": ["operation", "payload"],
                },
            ),
        )
    return tools


def dispatch_tool(
    name: str,
    arguments: dict[str, Any],
    ctx: ToolContext,
) -> dict[str, Any]:
    if name == "read_file":
        if ctx.dual_model:
            res = read_file(
                arguments["path"],
                workspace_root=ctx.workspace_root,
                refuse_over_lines=ctx.read_file_max_lines_dual,
            )
        else:
            res = read_file(arguments["path"], workspace_root=ctx.workspace_root)
        return res

    if name == "write_file":
        return write_file(
            arguments["path"],
            arguments["content"],
            workspace_root=ctx.workspace_root,
        )

    if name == "search_files":
        return search_files(
            arguments["pattern"],
            workspace_root=ctx.workspace_root,
            glob=str(arguments.get("glob") or "**/*.py"),
            max_matches=int(arguments.get("max_matches") or 50),
        )

    if name == "run_command":
        return run_command(
            arguments["argv"],
            workspace_root=ctx.workspace_root,
        )

    if name == "apply_patch":
        return apply_unified_diff(
            arguments["diff"],
            workspace_root=ctx.workspace_root,
        )

    if name == "small_model_tool":
        if not ctx.dual_model:
            return {"ok": False, "error": "small_model_tool_disabled_in_baseline"}
        op = arguments["operation"]
        payload = _coerce_tool_payload(arguments.get("payload"))
        if not payload.get("content") and payload.get("path"):
            loaded = read_file(
                str(payload["path"]),
                workspace_root=ctx.workspace_root,
            )
            if not loaded.get("ok"):
                return loaded
            payload["content"] = loaded["content"]
        if not payload.get("content"):
            return {
                "ok": False,
                "error": "payload_must_include_content_or_path",
            }
        result, meta = run_small_model_operation(
            client=ctx.client,
            model=ctx.small_model,
            operation=op,
            payload=payload,
        )
        if ctx.on_api_usage:
            ctx.on_api_usage(
                {
                    "role": "small",
                    "model": ctx.small_model,
                    "operation": f"small_model:{op}",
                    "input_tokens": meta["input_tokens"],
                    "output_tokens": meta["output_tokens"],
                    "wall_time_s": meta["wall_time_s"],
                }
            )
        return {"ok": True, "result": result, "usage": meta}

    if name == "finish":
        return {"ok": True, "finished": True, **arguments}

    return {"ok": False, "error": "unknown_tool", "name": name}


def parse_tool_calls(message: Any) -> list[dict[str, Any]]:
    """Normalize tool_calls from chat completion message."""
    out: list[dict[str, Any]] = []
    for tc in getattr(message, "tool_calls", None) or []:
        fn = tc.function
        args_raw = fn.arguments or "{}"
        try:
            args = json.loads(args_raw)
        except json.JSONDecodeError:
            args = {}
        out.append({"id": tc.id, "name": fn.name, "arguments": args})
    return out
