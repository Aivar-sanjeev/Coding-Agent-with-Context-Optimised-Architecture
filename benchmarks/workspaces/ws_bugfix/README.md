# Workspace: `ws_bugfix` (`bugfix_auth_middleware`)

## What it tests

Middleware-style header shaping breaks case-sensitive bearer auth until production code is fixed.

## Tech stack

Python 3, `pytest`, plain package layout under `app/`. Same platform stack as the agent: OpenAI Python SDK + NVIDIA NIM (see root `README.md` / `tasks/BENCHMARK_RESULTS.md`).

## Models, duration, wall clock (this workspace)

Update when you run **`tasks/specs/task_bugfix.json`** (dual or baseline). Copy from JSON: `models_used`, `timing.*`, `success`.

| Mode | Large model | Small model | Wall (s) | Agent loop (s) | Started (UTC) | Finished (UTC) | Success |
|------|-------------|-------------|----------|----------------|---------------|------------------|---------|
| dual | — | — | — | — | — | — | — |
| baseline | — | — | — | — | — | — | — |
