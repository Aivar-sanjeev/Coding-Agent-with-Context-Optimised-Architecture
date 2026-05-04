# Pull request: Add README, PR template, and gitignore hygiene

## Title

**docs: add README, PR description, and expand .gitignore**

## Summary

This change improves onboarding and mirrors a typical GitHub pull request: work is done on a **feature branch** (`docs/add-readme-and-pr-template`) and this file documents what reviewers should check before merging to **`main`**.

## What changed

- Added **`README.md`** at the repo root with setup, env notes, NVIDIA model troubleshooting, and commands for `task_runner` and `eval.run_table`.
- Added **`docs/PULL_REQUEST.md`** (this file) as a copy-pasteable PR body: title, summary, checklist, test plan.
- Expanded **`.gitignore`** to exclude virtualenvs, bytecode, and pytest caches (in addition to `.env`).

## Type of change

- [x] Documentation only  
- [ ] Bug fix  
- [ ] New feature  
- [ ] Breaking change  

## Test plan

- [ ] `pip install -r requirements.txt` succeeds in a clean venv  
- [ ] `python -m tasks.task_runner tasks/specs/task_bugfix.json dual` runs after `.env` is configured (smoke; may consume API credits)  
- [ ] `python -m pytest -q` from `benchmarks/workspaces/ws_refactor` still passes (no code change expected)  

## Merge checklist

- [ ] No secrets committed (`.env` remains ignored)  
- [ ] `README.md` links and commands verified on target OS (Windows / Linux)  

## Suggested git commands (maintainer / author)

```bash
git checkout main
git pull
git checkout -b docs/add-readme-and-pr-template
# … apply commits …
git push -u origin docs/add-readme-and-pr-template
```

Then open a compare URL on your host, e.g.:

`https://github.com/<org>/<repo>/compare/main...docs/add-readme-and-pr-template`

Paste this file’s **Title** and **Summary** sections into the PR description on GitHub/GitLab.
