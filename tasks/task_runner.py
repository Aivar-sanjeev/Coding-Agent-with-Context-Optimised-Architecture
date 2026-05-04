"""Load a JSON task spec, run the agent, optionally verify with a shell command."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.orchestrator import run_react_loop
from config import Settings, get_settings
from eval.metrics import MetricsSession

# Documented stack for README / benchmark tables (runtime does not change this list).
TECH_STACK_USED = [
    "Python 3",
    "OpenAI Python SDK (`openai`)",
    "NVIDIA NIM (OpenAI-compatible HTTPS API)",
    "pytest",
    "python-dotenv",
]


def load_spec(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_prepare(cmd: list[str] | None, *, cwd: Path) -> dict[str, Any]:
    if not cmd:
        return {"ok": True, "skipped": True}
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-50_000:],
            "stderr": proc.stderr[-50_000:],
        }
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)}


def run_verify(cmd: list[str] | None, *, cwd: Path) -> dict[str, Any]:
    return run_prepare(cmd, cwd=cwd)


def _timing_footer(
    *,
    settings: Settings,
    dual_model: bool,
    started_at: datetime,
    finished_at: datetime,
    wall_s: float,
    agent_metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "models_used": {
            "large": settings.large_model,
            "small": settings.small_model,
        },
        "tech_stack_used": list(TECH_STACK_USED),
        "mode": "dual" if dual_model else "baseline",
        "timing": {
            "started_at_utc": started_at.isoformat(),
            "finished_at_utc": finished_at.isoformat(),
            "wall_duration_total_s": round(wall_s, 3),
            "agent_loop_duration_s": agent_metrics.get("time_to_completion_s"),
        },
    }


def execute_task_spec(
    spec_path: Path,
    *,
    dual_model: bool,
    settings: Settings | None = None,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    spec = load_spec(spec_path)
    settings = settings or get_settings()
    workspace = (spec_path.parent / spec["workspace"]).resolve()
    if not workspace.is_dir():
        raise FileNotFoundError(f"workspace not found: {workspace}")

    prep = spec.get("prepare_command")
    if prep:
        pr = run_prepare(list(prep), cwd=workspace)
        if not pr["ok"]:
            finished_at = datetime.now(timezone.utc)
            wall_s = time.perf_counter() - t0
            return {
                "success": False,
                "phase": "prepare",
                "prepare": pr,
                "agent": {},
                "verify": {},
                **_timing_footer(
                    settings=settings,
                    dual_model=dual_model,
                    started_at=started_at,
                    finished_at=finished_at,
                    wall_s=wall_s,
                    agent_metrics={},
                ),
            }

    metrics = MetricsSession(settings=settings)
    agent_out = run_react_loop(
        workspace_root=workspace,
        task_user_message=str(spec["prompt"]),
        settings=settings,
        dual_model=dual_model,
        metrics=metrics,
    )

    verify_cmd = spec.get("verify_command")
    if verify_cmd:
        ver = run_verify(list(verify_cmd), cwd=workspace)
        objective = bool(ver.get("ok"))
    else:
        ver = {"ok": True, "skipped": True}
        objective = True

    finished_at = datetime.now(timezone.utc)
    wall_s = time.perf_counter() - t0
    success = objective and bool(agent_out.get("success"))
    agent_metrics = agent_out.get("metrics") or {}
    return {
        "success": success,
        "task_id": spec.get("id"),
        "dual_model": dual_model,
        "agent": agent_out,
        "verify": ver,
        "metrics": agent_metrics,
        **_timing_footer(
            settings=settings,
            dual_model=dual_model,
            started_at=started_at,
            finished_at=finished_at,
            wall_s=wall_s,
            agent_metrics=agent_metrics,
        ),
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) < 2:
        print(
            "Usage: python -m tasks.task_runner <spec.json> <dual|baseline>",
            file=sys.stderr,
        )
        return 2
    spec = Path(argv[0])
    mode = argv[1].lower()
    dual = mode == "dual"
    out = execute_task_spec(spec, dual_model=dual)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
