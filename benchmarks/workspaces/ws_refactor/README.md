# Workspace: `ws_refactor` (`refactor_order_processing`)

## What it tests

Refactor `app/orders.py` into smaller helpers while keeping `process_order` behaviour identical; `pytest` guards semantics.

## Tech stack

Python 3, `pytest`. Agent stack: OpenAI SDK + NVIDIA NIM (see `tasks/BENCHMARK_RESULTS.md`).

## Models, duration, wall clock (this workspace)

| Mode | Large model | Small model | Wall (s) | Agent loop (s) | Started (UTC) | Finished (UTC) | Success |
|------|-------------|-------------|----------|----------------|---------------|------------------|---------|
| dual | — | — | — | — | — | — | — |
| baseline | — | — | — | — | — | — | — |
