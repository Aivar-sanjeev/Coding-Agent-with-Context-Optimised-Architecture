"""
Run all task specs in baseline and dual modes and print a comparison table.

Usage (from coding_agent directory, with NVIDIA_API_KEY set):

  python -m eval.run_table
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.metrics import format_results_table
from tasks.task_runner import execute_task_spec


SPECS = [
    _ROOT / "tasks" / "specs" / "task_bugfix.json",
    _ROOT / "tasks" / "specs" / "task_feature.json",
    _ROOT / "tasks" / "specs" / "task_refactor.json",
]


def main() -> int:
    rows: list[dict[str, object]] = []
    for spec in SPECS:
        for mode, dual in (("baseline", False), ("dual", True)):
            try:
                out = execute_task_spec(spec, dual_model=dual)
            except Exception as e:
                out = {"success": False, "error": repr(e), "metrics": {}}
            m = out.get("metrics") or {}
            timing = out.get("timing") or {}
            models = out.get("models_used") or {}
            rows.append(
                {
                    "task": spec.stem,
                    "mode": mode,
                    "success": out.get("success", False),
                    "large_model": models.get("large", ""),
                    "small_model": models.get("small", ""),
                    "wall_total_s": timing.get("wall_duration_total_s", ""),
                    "started_utc": timing.get("started_at_utc", ""),
                    "finished_utc": timing.get("finished_at_utc", ""),
                    "large_input_tokens": m.get("total_input_tokens_large", ""),
                    "large_output_tokens": m.get("total_output_tokens_large", ""),
                    "small_in": m.get("total_input_tokens_small", ""),
                    "small_out": m.get("total_output_tokens_small", ""),
                    "cost_usd_est": m.get("total_cost_usd_estimate", ""),
                    "steps": m.get("steps_to_completion", ""),
                    "time_s": m.get("time_to_completion_s", ""),
                }
            )
    print(format_results_table(rows))
    print()
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
