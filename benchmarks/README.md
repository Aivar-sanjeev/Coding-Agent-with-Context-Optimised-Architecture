# Benchmarks

## Harness scripts

| Script | Spec |
|--------|------|
| `task_bugfix.py` | `tasks/specs/task_bugfix.json` |
| `task_feature.py` | `tasks/specs/task_feature.json` |
| `task_refactor.py` | `tasks/specs/task_refactor.json` |

Example: `python benchmarks/task_bugfix.py dual`

## Workspaces (`workspaces/`)

| Directory | Scenario |
|-----------|----------|
| `ws_bugfix/` | Failing pytest: `Authorization` mangled in middleware-style code; includes a long filler module for context-heavy runs. |
| `ws_feature/` | Missing `/health` route until the agent implements it. |
| `ws_refactor/` | Monolithic `process_order` to split; tests define behaviour. |

Each workspace has a short **`README.md`** with the same **models / timing / tech stack** fields as the aggregate log (update both when you record a run).

## Where to log timings and models

Central table: **[`../tasks/BENCHMARK_RESULTS.md`](../tasks/BENCHMARK_RESULTS.md)**.
