# Implementation Plan: Simple Todo Application

Status: DRAFT (automated). Produced by the implementation-planner. NOT approved by a human.
Traces to: `requirements.md` (FR-1..FR-8, AC1..AC6, T1..T7), `architecture.md`, `design-review.md` (Round 1, RESULT: PASS, automated review only).
Run branch: `story/todo-application-20261110090358-f560b4ea`
Delivery repo: `C:\Users\PalashManna\Desktop\Claude Capstone\claude-capstone`

Note on IDs: task IDs here are `T-01..`. They are distinct from the requirements' derived checks `T1..T7`, which are referenced as "check T1" etc.

## 1. Progress

All tasks below are PLANNED. Nothing is implemented or verified yet. Update the Status column only when work actually completes.

## 2. Assumptions (unconfirmed, labeled)

- PA1. Stack per design-review OD1: Python 3.10+, Flask, stdlib `sqlite3`, vanilla HTML/CSS/JS, pytest. This is an unconfirmed assumption (Q1) and is replaceable.
- PA2. Unknown PATCH fields are rejected with 400 (OD2).
- PA3. `created_at` is included, UTC ISO-8601 (OD3).
- PA4. No automated browser test. Refresh check T6 is MANUAL and must be recorded as manual in `verification.md` (OD4).
- PA5. Q2..Q9 remain unconfirmed assumptions, not blockers (OD5).
- PA6. Layout follows the architecture's non-binding suggestion: `app/` package, `tests/`, top-level `requirements.txt`.
- PA7. Existing `README.md` contains only a title line; it is preserved and extended, not replaced.
- PA8. Pinned versions are chosen by the implementer from versions installable at implementation time and recorded in `requirements.txt`.

## 3. Blockers

None. No unresolved scope question blocks implementation.

## 4. Planned layout (non-binding)

- `app/__init__.py` (factory `create_app`), `app/config.py`, `app/validation.py`, `app/repository.py`, `app/routes.py`
- `app/static/index.html`, `app/static/app.js`, `app/static/styles.css`
- `run.py` (entry point)
- `tests/conftest.py`, `tests/test_validation.py`, `tests/test_api.py`, `tests/test_security.py`, `tests/test_static.py`
- `requirements.txt`, `.gitignore`, `README.md`

## 5. Task list

Priority: P0 = foundation, P1 = core feature, P2 = hardening/docs/verification support. Order below is a valid execution order.

| ID | Pri | Title | Depends on | Status |
|----|-----|-------|------------|--------|
| T-01 | P0 | Repo hygiene: .gitignore and pinned requirements | none | PLANNED |
| T-02 | P0 | Config module and app factory skeleton | T-01 | PLANNED |
| T-03 | P0 | Validation module | T-02 | PLANNED |
| T-04 | P0 | Repository and schema | T-02 | PLANNED |
| T-05 | P0 | Test fixtures and validation unit tests | T-03 | PLANNED |
| T-06 | P1 | Repository tests incl. failure handling | T-04, T-05 | PLANNED |
| T-07 | P1 | API routes: list and create | T-03, T-04 | PLANNED |
| T-08 | P1 | API route: PATCH (edit and toggle) | T-07 | PLANNED |
| T-09 | P1 | API route: DELETE and id parsing | T-07 | PLANNED |
| T-10 | P1 | Error handling, 500 mapping, body size limit | T-08, T-09 | PLANNED |
| T-11 | P1 | API tests: CRUD, persistence, no-auth | T-08, T-09, T-10 | PLANNED |
| T-12 | P1 | Security hardening: Host allowlist, content-type, debug off | T-10 | PLANNED |
| T-13 | P1 | Security and edge-case tests | T-11, T-12 | PLANNED |
| T-14 | P1 | Frontend markup and styles | T-07 | PLANNED |
| T-15 | P1 | Frontend logic (app.js) | T-14, T-08, T-09 | PLANNED |
| T-16 | P1 | Static check test: no innerHTML | T-15 | PLANNED |
| T-17 | P2 | Run entry point and startup errors | T-12 | PLANNED |
| T-18 | P2 | README setup, run, test, limitations | T-15, T-17 | PLANNED |
| T-19 | P2 | Full test run and manual check script | T-13, T-16, T-18 | PLANNED |

## 6. Task details

### T-01 Repo hygiene: .gitignore and pinned requirements (P0)
- Prerequisites: none.
- Files: `.gitignore`, `requirements.txt`.
- Work: `.gitignore` excludes the SQLite db file (`*.db`, data dir), virtualenvs (`venv/`, `.venv/`), caches (`__pycache__/`, `*.pyc`, `.pytest_cache/`), editor/OS files. Do NOT ignore the lifecycle `.md` files. `requirements.txt` pins Flask and pytest with exact `==` versions (L8, PA8).
- Done when: `git check-ignore` confirms `todo.db`, `.venv/x`, `__pycache__/x` are ignored; `requirements.txt` has exact `==` pins for each entry; `pip install -r requirements.txt` succeeds in a fresh venv (record if not run).

### T-02 Config module and app factory skeleton (P0)
- Prerequisites: T-01.
- Files: `app/__init__.py`, `app/config.py`.
- Work: `create_app(db_path=None, testing=False)` factory. Config reads DB path (env var, default `todo.db` in a data dir), host (default `127.0.0.1`), port, and a debug flag from env. Debug is OFF by default and only enabled by an explicit env flag (M1). Sets `MAX_CONTENT_LENGTH` (~10 KB). No secrets.
- Done when: `create_app()` returns an app with no routes errors; with no env set, config reports debug False and host `127.0.0.1`; factory accepts a temp DB path (verified in T-05 and T-06).

### T-03 Validation module (P0)
- Prerequisites: T-02.
- Files: `app/validation.py`.
- Work: single place for rules. Description must be `str` (explicit type check), trimmed, 1..255 Unicode code points (L2). `completed` must be a real boolean using `isinstance(x, bool)` so `1`, `0`, `"true"` fail (M6). Payload must be a JSON object. PATCH payload requires at least one known field; unknown fields rejected (OD2); `null` for a known field rejected (L1). One error shape: message string.
- Done when: functions exist and are exercised by T-05 tests, all passing.

### T-04 Repository and schema (P0)
- Prerequisites: T-02.
- Files: `app/repository.py`.
- Work: schema `tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)` created on startup if absent. Operations: create, list (ordered by `id`), get, update, delete. Parameterised SQL only. Per-request connection with a timeout of a few seconds; explicit commit and rollback (M5). Converts `completed` 0/1 to JSON boolean; task shape `{id, description, completed, created_at}` (L4). `created_at` UTC ISO-8601 (OD3). Optional CHECK on `length(description)` must use `length()` consistently (L2). WAL optional.
- Done when: repository functions work against a temp DB; no string-built SQL (grep for f-string/format/concatenation in SQL finds none); verified by T-06.

### T-05 Test fixtures and validation unit tests (P0)
- Prerequisites: T-03.
- Files: `tests/conftest.py`, `tests/test_validation.py`.
- Work: fixtures create an app on a pytest `tmp_path` DB plus a test client. Validation tests: empty, whitespace-only, trimmed result, exactly 255 OK, 256 rejected (and multi-byte characters counted as code points), `description` as `123`, `null`, list; `completed` as `1`, `0`, `"true"`, `null`; PATCH with `{}`, unknown field, non-object body (M6, L1, L2).
- Done when: `pytest tests/test_validation.py` passes.

### T-06 Repository tests incl. failure handling (P1)
- Prerequisites: T-04, T-05.
- Files: `tests/test_repository.py`.
- Work: create/list/get/update/delete; default pending; list ordered by id; `created_at` present and parseable as UTC; boolean conversion; schema auto-created when the DB file is missing; data persists when a new app instance opens the same file; large-integer and nonexistent ids return "not found" and do not raise (L3); a simulated DB failure rolls back (M5).
- Done when: `pytest tests/test_repository.py` passes.

### T-07 API routes: list and create (P1)
- Prerequisites: T-03, T-04.
- Files: `app/routes.py`, `app/__init__.py` (register blueprint).
- Work: `GET /api/tasks` returns 200 array. `POST /api/tasks` validates, creates pending task, returns 201 and the task. Serves `index.html` at `/`. POST requires `Content-Type: application/json` else 415, no `force=True` (M3). Malformed JSON returns 400. Error body `{"error": "<message>"}`.
- Done when: manual call via test client shows 200/201/400/415 as stated; covered by T-11.

### T-08 API route: PATCH edit and toggle (P1)
- Prerequisites: T-07.
- Files: `app/routes.py`.
- Work: `PATCH /api/tasks/<id>` with `description?` and/or `completed?`. Validation per T-03 (at least one known field, unknown rejected with 400, strict types). 200 and updated task; 404 for unknown id; 415 unless `application/json` (M3).
- Done when: covered by T-11 tests for edit, toggle both ways, and rejection cases.

### T-09 API route: DELETE and id parsing (P1)
- Prerequisites: T-07.
- Files: `app/routes.py`.
- Work: `DELETE /api/tasks/<id>` returns 204, or 404 for unknown id. `<id>` parsed as a positive integer; non-integer, zero, negative, or overflow-sized values return 404 and never 500 (L3). No CORS headers are added.
- Done when: covered by T-11 tests including id `0`, `-1`, `abc` and `99999999999999999999`.

### T-10 Error handling, 500 mapping, body size limit (P1)
- Prerequisites: T-08, T-09.
- Files: `app/routes.py` or `app/__init__.py` (error handlers).
- Work: JSON error handlers for 400, 404, 405, 413, 415, 500 using the single error shape. Database errors map to a generic 500 with no SQL, paths or stack trace in the body; details logged server-side only (M5).
- Done when: a test that forces a repository exception receives 500 with generic JSON and the body contains no SQL text or file path; oversized body returns 413.

### T-11 API tests: CRUD, persistence, no-auth (P1)
- Prerequisites: T-08, T-09, T-10.
- Files: `tests/test_api.py`.
- Work: tests mapped to requirement checks. T1: add returns pending. T2: list count equals N. T3: toggle and toggle back, status persists. T4: edit updates list and stored value. T5: delete removes from list and storage. T6 (server side): a new app instance on the same DB file returns the same tasks and statuses. T7: all calls made with no credentials succeed. Also: task JSON shape, `completed` is a JSON boolean, ordering by id, HTML in description returned verbatim as JSON.
- Done when: `pytest tests/test_api.py` passes.

### T-12 Security hardening: Host allowlist, content-type, debug off (P1)
- Prerequisites: T-10.
- Files: `app/__init__.py` (or `app/security.py`), `app/config.py`.
- Work: `before_request` check that the `Host` header is in an allowlist (`127.0.0.1`, `localhost`, with configured port); otherwise 400 or 403 JSON (M2). Confirm strict content-type enforcement stays on POST and PATCH (M3). Confirm debug default is off and enabled only by an explicit env flag (M1). Add standard response headers if cheap (for example `X-Content-Type-Options: nosniff`), optional.
- Done when: covered by T-13 tests; reading the default run path shows no `debug=True`.

### T-13 Security and edge-case tests (P1)
- Prerequisites: T-11, T-12.
- Files: `tests/test_security.py`.
- Work: bad `Host` header rejected, allowed hosts accepted (M2). POST and PATCH with `text/plain` and a JSON body return 415 (M3). DELETE and PATCH carry no CORS headers. Default config has debug False (M1). 500 body generic (M5, if not already in T-11). Request body over limit returns 413. Malformed JSON returns 400.
- Done when: `pytest tests/test_security.py` passes.

### T-14 Frontend markup and styles (P1)
- Prerequisites: T-07.
- Files: `app/static/index.html`, `app/static/styles.css`.
- Work: semantic HTML. Add form with a labelled input (`maxlength=255`, `required`), a submit button, a task list container, an error message region (`role="alert"` or `aria-live`). Controls are keyboard-operable (L6). Simple, readable styling (NFR-1). No inline scripts.
- Done when: page loads at `/` in the test client with 200 and references `app.js` and `styles.css`; every input has an associated label (checked by review of the file).

### T-15 Frontend logic (app.js) (P1)
- Prerequisites: T-14, T-08, T-09.
- Files: `app/static/app.js`.
- Work: on load, `GET /api/tasks` and render. Add via `POST`. Toggle via `PATCH {completed: !current}`. Inline edit via `PATCH {description}` (save and cancel, keyboard friendly). Delete via `DELETE` immediately with no confirmation (A4). Render ALL task text with `textContent` and DOM APIs, never `innerHTML`, `outerHTML` or `insertAdjacentHTML` (M4). On failure keep prior state and show a generic error; on 404 show the message and reload the list. Client-side checks are for feedback only. Fetches send `Content-Type: application/json`. Empty-state message when no tasks.
- Done when: T-16 passes; the manual browser check in T-19 is performed and recorded honestly.

### T-16 Static check test: no innerHTML (P1)
- Prerequisites: T-15.
- Files: `tests/test_static.py`.
- Work: read `app/static/app.js` and assert it contains none of `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval(`. Also assert `index.html` has no inline `<script>` code and no inline event handler attributes (M4).
- Done when: `pytest tests/test_static.py` passes. This does NOT prove browser rendering; that remains a manual check.

### T-17 Run entry point and startup errors (P2)
- Prerequisites: T-12.
- Files: `run.py`, `app/config.py` if needed.
- Work: starts the app bound to `127.0.0.1` with debug from config (default off). Clear one-line startup error (no traceback dump of internals) if the port is in use or the data directory is not writable (L7). Corrupt DB file produces a clear log message and a non-zero exit, no auto-repair. DB schema auto-created when the file is missing.
- Done when: `python run.py` starts and `GET /api/tasks` returns 200 (record whether this was run); a second instance on the same port prints the clear error; default path does not set debug.

### T-18 README setup, run, test, limitations (P2)
- Prerequisites: T-15, T-17.
- Files: `README.md` (extend; keep the existing title line, PA7).
- Work: sections for overview, prerequisites (Python 3.10+), venv creation and activation (Windows PowerShell and POSIX), `pip install -r requirements.txt`, run command and URL, environment variables (DB path, host, port, debug flag), running tests, API summary, project layout. Note that `requirements.txt` is the Python dependency list and unrelated to the story's `requirements.md` (L8). Limitations: no auth and not for public exposure, local dev server only, DNS-rebinding residual risk and Host allowlist, last-write-wins, no pagination or migrations, delete has no undo, stack and decisions are unconfirmed assumptions, T6 refresh check is manual. No secrets.
- Done when: every command in the README matches actual files and env var names (reviewed against the code); required sections present.

### T-19 Full test run and manual check script (P2)
- Prerequisites: T-13, T-16, T-18.
- Files: `README.md` (short "Manual checks" section) or `docs/manual-checks.md` (new file, optional).
- Work: run the full `pytest` suite and record the real result. Document the manual browser checklist: add, view, toggle both ways, edit, delete, refresh persistence (T6), stored HTML text such as `<b>x</b>` displays literally, no login prompt (T7). The implementation agent must NOT mark manual checks as passed unless a browser run actually occurred; otherwise record them as MANUAL, NOT RUN for `verification.md`.
- Done when: `pytest` exits 0 with the output recorded; the manual checklist exists and is labelled MANUAL.

## 7. Design review traceability

| Item | Handled in |
|------|-----------|
| M1 debug off by default | T-02, T-12, T-13, T-17 |
| M2 Host allowlist | T-12, T-13, T-18 (residual risk documented) |
| M3 strict application/json, no force | T-07, T-08, T-12, T-13 |
| M4 no innerHTML automated check | T-15, T-16 |
| M5 timeout, rollback, generic 500 test | T-04, T-06, T-10, T-13 |
| M6 strict types and tests | T-03, T-05 |
| L1 PATCH edge cases | T-03, T-05, T-08 |
| L2 code point counting | T-03, T-04, T-05 |
| L3 id edge cases | T-06, T-09, T-11 |
| L4 response shape | T-04, T-11 |
| L6 accessibility | T-14, T-15 |
| L7 startup errors | T-17 |
| L8 pinned deps and README note | T-01, T-18 |
| OD1 stack accepted (assumption) | PA1, all |
| OD2 reject unknown PATCH fields | T-03, T-08 |
| OD3 created_at | T-04, T-06 |
| OD4 refresh check manual | T-19 |
| OD5 Q2..Q9 stay assumptions | Section 2 |

## 8. Requirement coverage

| Requirement | Tasks |
|-------------|-------|
| FR-1 add | T-07, T-15 |
| FR-2 view | T-07, T-15 |
| FR-3 toggle | T-08, T-15 |
| FR-4 edit | T-08, T-15 |
| FR-5 delete | T-09, T-15 |
| FR-6 persistence | T-04, T-11, T-19 (manual) |
| FR-7 DB via backend | T-04, T-07..T-09 |
| FR-8 no auth | T-11 (no-credential calls), T-18 (limitation) |
| NFR-A1 validation and feedback | T-03, T-15 |
| NFR-A2 README | T-18 |
| NFR-A3 tests | T-05, T-06, T-11, T-13, T-16, T-19 |
| NFR-A4 no secrets | T-01, T-02, T-18 |

## 9. Out of scope (carried from requirements section 9)

Accounts, due dates, priorities, tags, search, filtering, reordering, deployment, native mobile, automated browser tests (OD4), WAL tuning, migrations.

## 10. Approval status

- Plan review: NOT PERFORMED. Plan approval: NOT APPROVED by a human. Automated draft only.
