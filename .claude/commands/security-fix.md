Implement the next pending security fix from TODO.md in the RAG chatbot codebase.

## Repo context

- Repo root: `/home/mb/Desktop/AI/claudecode_course/code/starting-ragchatbot-codebase`
- Backend: `backend/` (FastAPI, Python, run with `uv run`)
- Frontend: `frontend/` (vanilla JS, no build step)
- Config: `backend/config.py` — all tunable settings in a `Config` dataclass
- Tests: `cd backend && uv run pytest` (run from repo root as `cd backend && uv run pytest`)
- Key rule: always use `uv run` to execute Python

## Protocol

1. Read `TODO.md` at the repo root.
2. Find the **first task** whose heading contains `[pending]`.
3. Change its status from `[pending]` to `[in-progress]` in `TODO.md`.
4. Read the relevant source file(s) listed in the task to understand the current code.
5. Implement the fix exactly as described in the task body. Follow the concrete instructions — do not over-engineer or add scope beyond what the task describes.
6. Run tests: `cd /home/mb/Desktop/AI/claudecode_course/code/starting-ragchatbot-codebase/backend && uv run pytest`
   - If tests pass (or only pre-existing failures): proceed.
   - If your change introduced new test failures: fix them before continuing.
   - If there are no tests yet: note this and proceed.
7. Mark the task `[done]` in `TODO.md` (change `[in-progress]` → `[done]`).
8. Tell the user: **"Task N is done. Run `/clear` then `/security-fix` to tackle the next one."**

## Failure handling

- If a fix is ambiguous, read the surrounding code carefully — the task description plus the actual code should be enough to determine intent.
- Do not skip a task because it seems hard. Work through it.
- If tests were already failing before your change (pre-existing failures), that is acceptable — note it and mark the task done anyway.
- If you cannot determine whether a test failure is pre-existing, check `git stash && uv run pytest` to get a baseline, then `git stash pop` and re-apply your fix.
