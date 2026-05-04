"""
Bugfix benchmark harness.

Prepares nothing (workspace ships in failing state). Run from repo root:

  cd coding_agent
  python benchmarks/task_bugfix.py dual
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tasks.task_runner import execute_task_spec


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    mode = (argv[0] if argv else "dual").lower()
    dual = mode != "baseline"
    spec = _ROOT / "tasks" / "specs" / "task_bugfix.json"
    out = execute_task_spec(spec, dual_model=dual)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
