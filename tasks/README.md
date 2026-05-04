# Tasks

JSON specs live in **`specs/`**. The runner loads a spec, optionally prepares the workspace, runs the **ReAct agent**, then runs **`verify_command`** (usually `pytest`).

## Specs

| File | `id` | Workspace |
|------|------|-------------|
| `specs/task_bugfix.json` | `bugfix_auth_middleware` | `benchmarks/workspaces/ws_bugfix` |
| `specs/task_feature.json` | `feature_health_endpoint` | `benchmarks/workspaces/ws_feature` |
| `specs/task_refactor.json` | `refactor_order_processing` | `benchmarks/workspaces/ws_refactor` |

## Runner output (for README tables)

Each run prints JSON including:

| Field | Meaning |
|-------|---------|
| `models_used` | `large` / `small` model ids from `.env` |
| `tech_stack_used` | Fixed list from `task_runner.py` |
| `timing.started_at_utc` | ISO-8601 UTC when the run began |
| `timing.finished_at_utc` | ISO-8601 UTC when the run ended |
| `timing.wall_duration_total_s` | Wall seconds for prepare + agent + verify |
| `timing.agent_loop_duration_s` | Orchestrator wall seconds (from agent metrics) |
| `success` | Objective verify + agent `finish` |

## Benchmark results table

Maintained copy of the run matrix: **[`BENCHMARK_RESULTS.md`](BENCHMARK_RESULTS.md)**.

## Commands

```bash
# From repo root coding_agent/
python -m tasks.task_runner tasks/specs/task_bugfix.json dual
python -m tasks.task_runner tasks/specs/task_feature.json baseline
```
