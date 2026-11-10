# Verification: Simple Todo Application

Status: automated verification only. This is not human acceptance. Date: 2026-11-10.
Branch (checked with `git branch --show-current`): `story/todo-application-20261110090358-f560b4ea`.
Nothing was committed, pushed or staged by this step.

## 1. Commands run and real results

| # | Command | Result |
|---|---------|--------|
| 1 | `<scratchpad>\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` (cwd = delivery repo) | `195 passed in 1.75s` (0 failed) |
| 2 | `node --check app/static/app.js` | exit 0 (syntax OK; syntax check only, not a runtime test) |
| 3 | Smoke script `<scratchpad>\smoke.py`: starts `python run.py` with `TODO_DB_PATH=<scratchpad>\smoke_data\todo.db` and `TODO_PORT=60326` (free, non-default). It calls the API with python urllib on `http://127.0.0.1:60326`. | All steps behaved as expected (details in section 2) |
| 4 | `python -m pip_audit --version` | `No module named pip_audit`. NOT RUN, tool not installed (nothing was installed). |
| 5 | `git status --short --ignored` | No `.db` or sqlite files in the repo. Only ignored Python caches appear: `.pytest_cache/` (existing from earlier runs; this run used `-p no:cacheprovider`), `app/__pycache__/`, `tests/__pycache__/`. All are git-ignored. |

The smoke DB was written under the scratchpad, outside the repo. The server stopped only by its own PID (19380, then 5416). After the final stop, a request to the port failed with `URLError`, so nothing listens on it.

## 2. Smoke run: actual responses (output quality)

- `POST /api/tasks {"description":"Buy milk"}` returned 201 `{"completed":false,"created_at":"2026-11-10T09:23:49+00:00","description":"Buy milk","id":1}`. The new task defaults to pending (A3).
- A second POST ("Walk dog") returned 201 with id 2.
- `POST` with a whitespace-only description returned 400 `{"error":"description must not be empty."}` (A2).
- `GET /api/tasks` returned 200 with a JSON array of 2 tasks in creation order (A9).
- `PATCH /api/tasks/1 {"completed":true}` returned 200 with `completed:true`.
- `PATCH /api/tasks/1 {"description":"Buy oat milk"}` returned 200 with the new description. `completed` stayed true.
- `DELETE /api/tasks/2` returned 204 with an empty body. A later GET listed only task 1.
- `PATCH` and `DELETE` on a 23-digit id both returned 404 (the review finding 1 fix works at runtime).
- After a server restart on the same DB file, `GET /api/tasks` returned task 1 ("Buy oat milk", completed true). Persistence in SQLite across process restarts is confirmed.
- Responses are well-formed JSON with consistent fields (`id`, `description`, `completed`, `created_at`). Errors use `{"error": ...}`.
- The toggle-back (completed to pending) was not exercised in the smoke run. The automated suite covers it (see section 3).

## 3. Acceptance-criteria checklist

"API-level" means verified through HTTP/API calls or tests, not through the browser UI.

| ID | Criterion | Evidence | Status |
|----|-----------|----------|--------|
| AC1 / T1 | Add a task, which appears as pending | Smoke POST 201 and pytest suite (API-level) | PASS, API-level only. UI form not exercised in a browser. |
| AC2 / T2 | View all tasks in a list | Smoke GET returned N tasks and pytest (API-level) | PASS, API-level only. List rendering not checked in a browser. |
| AC3 / T3 | Toggle completed and pending, persisted | Smoke PATCH toggle and persistence after restart. The toggle-back is covered by the pytest suite (195 passed). I did not read the individual test cases, so I did not verify they cover the toggle-back. | PASS (API-level). The toggle-back is not confirmed by a runtime smoke call. |
| AC4 / T4 | Edit a description, with the stored value updated | Smoke PATCH edit and persistence after restart | PASS, API-level only |
| AC5 / T5 | Delete a task from the list and from storage | Smoke DELETE 204 and the follow-up GET | PASS, API-level only |
| AC6 / T6 | Tasks remain after a browser refresh | Persistence across a server restart verified at the API/DB level. The browser-refresh check itself was NOT RUN (no browser). | PARTIAL. MANUAL check NOT RUN; see `docs/manual-checks.md`. |
| T7 | Works without login | All API calls were made with no credentials | PASS, API-level only |

Items NOT RUN (manual, no browser used):
- T6 browser refresh.
- Keyboard and focus behaviour.
- Visual and rendering checks, and the "simple and user-friendly" UI requirement (NFR-1).
- Checklist: `C:\Users\PalashManna\Desktop\Claude Capstone\claude-capstone\docs\manual-checks.md`.
- `node --check` only proves the JS parses. The frontend logic (`app.js`) has no runtime test in a browser or DOM.

## 4. Code review linkage

- Code review round 1 outcome: PASS (automated, not human approval).
- Findings 1-2 were fixed after the review:
  - Huge-id 404 fix in `app/routes.py` `_parse_id`. The code now rejects ids longer than 19 digits, and the smoke run confirmed 404.
  - Redundant if/else removed in the `startEdit` function in `app.js`. This was not runtime-checked in a browser; only the `node --check` syntax check ran.
- The post-review delta is small. It was covered by the full test run in section 1, which was run after the fixes.
- Low findings 3-5 are unresolved and accepted as known limitations:
  - 3. Dependency vulnerability scan not run (`pip-audit` is not installed).
  - 4. Optional SQL helper duplication left as is.
  - 5. IPv6 `[::1]` is rejected by design (the Host header allowlist is `127.0.0.1` and `localhost` only). README check: the README documents the `127.0.0.1`/`localhost` allowlist (lines 74-75), but it does NOT state that IPv6 `[::1]` is rejected (no `::1` or IPv6 mention found). This is a documentation gap and is reported as a low-severity limitation, not fixed here.

## 5. Limitations

- No browser was available, so UI behaviour is unverified at runtime (see the section 3 list).
- Acceptance coverage is API-level; no end-to-end UI test exists.
- Dependency vulnerability scan was NOT RUN.
- No CI was available or used. No CI evidence is claimed.
- Single smoke run on Windows only. Concurrency and performance were not tested.
- Requirements are an unreviewed draft with unconfirmed assumptions (A1-A9); there is no human approval.

## 6. Outcome

All automated checks that ran passed. The manual browser, keyboard and rendering checks are NOT RUN and remain for a human to perform. The README gap on `[::1]` is noted as a low limitation.

Automated verification outcome: PASS (not human acceptance).
