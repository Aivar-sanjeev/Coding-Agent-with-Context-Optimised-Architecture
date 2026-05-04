# Benchmark task runs (metrics log)

Each row is one **`python -m tasks.task_runner <spec> <dual|baseline>`** invocation. After you run a task, copy from the printed JSON:

- `models_used.large` / `models_used.small`
- `timing.started_at_utc` → `timing.finished_at_utc`
- `timing.wall_duration_total_s` (entire run: agent + verify)
- `timing.agent_loop_duration_s` (orchestrator only, from `metrics.time_to_completion_s`)
- `tech_stack_used` (fixed list; same for all rows unless you change the runner)
- `success`

Default model names below match **`.env.example`**; your real runs use whatever is in **`.env`**.

| Task ID | Mode | Large model | Small model | Tech stack | Wall (s) | Agent loop (s) | Started (UTC) | Finished (UTC) | Success |
|---------|------|-------------|-------------|------------|----------|----------------|---------------|------------------|---------|
| `bugfix_auth_middleware` | dual | `meta/llama-3.1-70b-instruct` | `meta/llama-3.1-8b-instruct` | Python 3, OpenAI SDK, NVIDIA NIM, pytest, python-dotenv | — | — | — | — | — |
| `bugfix_auth_middleware` | baseline | `meta/llama-3.1-70b-instruct` | `meta/llama-3.1-8b-instruct` | same | — | — | — | — | — |
| `feature_health_endpoint` | dual | `meta/llama-3.1-70b-instruct` | `meta/llama-3.1-8b-instruct` | same | — | — | — | — | — |
| `feature_health_endpoint` | baseline | `meta/llama-3.1-70b-instruct` | `meta/llama-3.1-8b-instruct` | same | — | — | — | — | — |
| `refactor_order_processing` | dual | `meta/llama-3.1-70b-instruct` | `meta/llama-3.1-8b-instruct` | same | — | — | — | — | — |
| `refactor_order_processing` | baseline | `meta/llama-3.1-70b-instruct` | `meta/llama-3.1-8b-instruct` | same | — | — | — | — | — |

Replace `—` with values from your machine after runs. **`baseline`** mode still lists the small model id from config (it is not called for tool work, but remains your configured small endpoint).
