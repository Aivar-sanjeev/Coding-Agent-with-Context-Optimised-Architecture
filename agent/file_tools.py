"""Filesystem helpers for the coding agent (read / write / search / patch)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


def _resolve_under_root(path: str | Path, workspace_root: Path) -> Path:
    p = (workspace_root / Path(path)).resolve()
    root = workspace_root.resolve()
    if root not in p.parents and p != root:
        raise ValueError(f"Path escapes workspace: {path}")
    return p


def count_lines(path: str, *, workspace_root: Path) -> dict[str, Any]:
    fp = _resolve_under_root(path, workspace_root)
    if not fp.is_file():
        return {"ok": False, "error": f"Not a file: {path}"}
    n = 0
    with fp.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            n += chunk.count(b"\n")
    return {"ok": True, "path": str(fp.relative_to(workspace_root)), "line_count": n}


def read_file(
    path: str,
    *,
    workspace_root: Path,
    max_lines: int | None = None,
    refuse_over_lines: int | None = None,
) -> dict[str, Any]:
    """Read a text file. If max_lines is set, only the first max_lines are returned."""
    fp = _resolve_under_root(path, workspace_root)
    if not fp.is_file():
        return {"ok": False, "error": f"Not a file: {path}"}
    if refuse_over_lines is not None:
        lc = count_lines(path, workspace_root=workspace_root)
        if lc.get("ok") and int(lc["line_count"]) > refuse_over_lines:
            return {
                "ok": False,
                "error": "file_too_large_for_direct_read",
                "line_count": lc["line_count"],
                "path": lc["path"],
                "max_lines": refuse_over_lines,
                "hint": "Call small_model_tool with payload.path set to this file plus operation and query.",
            }
    text = fp.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    truncated = False
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
        text = "\n".join(lines) + "\n"
    return {
        "ok": True,
        "path": str(fp.relative_to(workspace_root)),
        "content": text,
        "line_count": len(lines),
        "truncated": truncated,
    }


def write_file(path: str, content: str, *, workspace_root: Path) -> dict[str, Any]:
    fp = _resolve_under_root(path, workspace_root)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8", newline="\n")
    return {"ok": True, "path": str(fp.relative_to(workspace_root))}


def search_files(
    pattern: str,
    *,
    workspace_root: Path,
    glob: str = "**/*.py",
    max_matches: int = 50,
) -> dict[str, Any]:
    """Regex search across files under workspace."""
    rx = re.compile(pattern)
    matches: list[dict[str, Any]] = []
    for f in sorted(workspace_root.glob(glob)):
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(f.relative_to(workspace_root))
        for i, line in enumerate(text.splitlines(), start=1):
            if rx.search(line):
                matches.append(
                    {"file": rel, "line": i, "text": line.strip()[:500]}
                )
                if len(matches) >= max_matches:
                    return {"ok": True, "matches": matches, "truncated": True}
    return {"ok": True, "matches": matches, "truncated": False}


def run_command(
    command: list[str] | str,
    *,
    workspace_root: Path,
    timeout_s: int = 300,
) -> dict[str, Any]:
    if isinstance(command, str):
        cmd = command
        shell = True
        argv: list[str] = []
    else:
        cmd = None
        shell = False
        argv = command
    try:
        proc = subprocess.run(
            argv if not shell else cmd,
            cwd=workspace_root,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return {
            "ok": True,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-200_000:],
            "stderr": proc.stderr[-200_000:],
        }
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "error": "timeout", "detail": str(e)}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)}


def apply_unified_diff(
    diff_text: str,
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    """
    Best-effort patch application using `patch` if available, else return error.
    On Windows, patch may be missing; callers can fall back to write_file.
    """
    try:
        proc = subprocess.run(
            ["patch", "-p1", "--forward", "--reject-file=-", "--no-backup-if-mismatch"],
            cwd=workspace_root,
            input=diff_text,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "patch_binary_missing",
            "hint": "Use write_file with full content or install patch (Git Bash).",
        }
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)}
