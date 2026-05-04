"""Baseline agent: large model + tools without small_model_tool."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.orchestrator import run_react_loop
from config import get_settings
from eval.metrics import MetricsSession


def run_baseline(workspace_root: Path, task_user_message: str) -> dict:
    settings = get_settings()
    metrics = MetricsSession(settings=settings)
    return run_react_loop(
        workspace_root=workspace_root,
        task_user_message=task_user_message,
        settings=settings,
        dual_model=False,
        metrics=metrics,
    )
