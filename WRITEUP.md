# Context-Optimised Dual-Model Coding Agent — Write-up

## 1. Framing: context management as a capability

Most coding agents treat long logs, large files, and multi-file search results as unavoidable prompt bloat. Here, **context management is a first-class capability**: the large model plans and edits, while a cheap, high-context small model is invoked as a **tool** to shrink raw I/O into structured JSON the large model can parse. That keeps the orchestrator’s transcript focused on decisions and patches instead of megabytes of incidental text.

## 2. Design decisions: interface contract

**Delegated to the small model** (via `small_model_tool`): summarising large bodies, extracting line-level evidence, triaging test output, classifying diffs, dependency-style reference listing from supplied excerpts, and summarising stack traces. Each operation uses a **tight system prompt** and returns **JSON only** (with `json_object` mode when supported, and a parse fallback).

**Kept on the large model**: architecture, multi-step planning, choosing edits, constructing patches, running commands, and final `finish` with an explicit success flag.

**Enforcement**: In dual mode, `read_file` refuses files over `READ_FILE_MAX_LINES_DUAL` so the large model must route bulk inspection through `small_model_tool` (including `payload.path` so the tool can load the file without the large model ever seeing the full text).

## 3. Measurement (placeholder for your runs)

Run (with `NVIDIA_API_KEY` set):

```text
cd coding_agent
python -m eval.run_table
```

You should record per task and mode: `total_input_tokens_large`, estimated `total_cost_usd`, `steps_to_completion`, `success`, and `time_to_completion_s`. Paste the generated markdown table here after runs. Expect the largest **large-model input token** reductions on the bugfix workspace (includes a long filler module) when the agent complies with the `small_model_tool` routing.
