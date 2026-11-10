# Design Review: Simple Todo Application

Review round: 1
Reviewer: design-reviewer (automated specialist review)
Reviewed: `architecture.md` against `requirements.md`
Run branch: `story/todo-application-20261110090358-f560b4ea`
Outcome: **PASS** (no unresolved blocking or high findings)
Approval status: This is an automated review. It is NOT human approval. Architecture and requirements remain NOT APPROVED by a human.

## 1. Summary

The architecture covers FR-1..FR-8 and T1..T7. Component boundaries are clear (UI, routes, validation, repository, SQLite). The data flow, trust boundaries and failure table are consistent with the requirements. Remaining issues are medium and low hardening or clarity items. The planner should carry them as explicit tasks.

## 2. Traceability check

| Requirement | Covered by | Result |
|---|---|---|
| FR-1 add | POST /api/tasks, validation, UI form | Covered |
| FR-2 view | GET /api/tasks, list render | Covered |
| FR-3 toggle both ways | PATCH `completed` true/false | Covered |
| FR-4 edit | PATCH `description` | Covered |
| FR-5 delete | DELETE /api/tasks/<id> | Covered |
| FR-6 persistence | SQLite file, load on page load | Covered |
| FR-7 DB via backend | Flask + SQLite | Covered |
| FR-8 no auth | No auth; localhost binding; limitation noted | Covered |
| NFR-1 simple UI | Vanilla UI; verified only by review (stated) | Covered, subjective |
| NFR-A1..A4 (assumed) | Validation, config, pytest, no secrets | Covered |
| T1..T7 | Section 10 of architecture | Covered; T6 browser check is manual unless automated |

## 3. Findings

### Blocking
None.

### High
None.

### Medium

- M1. Flask debug mode. The Werkzeug debugger allows code execution and would be dangerous on an unauthenticated API. The architecture does not say debug is off.
  Mitigation: state that debug is disabled by default. Enable it only through an explicit environment flag. Add a check that the default run path does not enable debug.
- M2. Localhost with no auth: DNS rebinding and other local pages. The CSRF and CORS reasoning in section 7.6 is sound for cross-origin simple requests. It does not cover DNS rebinding, where a hostile page reaches `127.0.0.1` under an attacker-controlled hostname.
  Mitigation: validate the `Host` header against an allowlist (`127.0.0.1`, `localhost` and the configured port). Reject others with 400 or 403. Add this to the limitations text as a residual risk. This is cheap to implement and test.
- M3. Strict content-type enforcement is the only CSRF defence. The architecture relies on `Content-Type: application/json`, but `request.get_json(force=True)` or a lenient parse would undo it.
  Mitigation: POST and PATCH must return 415 unless the content type is `application/json`. Do not use `force=True`. Add a test with `text/plain` and a JSON body. DELETE is a non-simple method, so a preflight is required and no CORS is granted. Keep it that way.
- M4. Stored XSS defence is verified only by a manual check. Security-critical rendering has no automated test, and the only automated test covers server JSON.
  Mitigation: add a static check that `app.js` contains no `innerHTML`, `outerHTML` or `insertAdjacentHTML` for task data. Alternatively add a lightweight DOM test. Record the manual browser check as manual, not as passed, if it is the only evidence.
- M5. SQLite concurrency and connection handling. "Locked" is listed as a failure, but nothing sets a busy timeout. A per-request connection with a default timeout is acceptable for this scale. Rollback and the 500 mapping depend on it.
  Mitigation: use a connection timeout of a few seconds. Use `with` or explicit commit and rollback. Add a test that a repository failure produces a generic 500 with no SQL or path in the body. Enabling WAL is optional.
- M6. Validation type pitfalls. In Python, `bool` is a subclass of `int`. A loose check could accept `1` or `0` for `completed`, or `true` as a description.
  Mitigation: check `type(x) is bool` or `isinstance(x, bool)` explicitly for `completed`, and require `str` for `description`. Add tests for `completed: 1`, `completed: "true"`, `description: 123` and `description: null`.

### Low

- L1. PATCH edge cases. An empty body, `{}`, or a body that is not an object (array, string) needs a defined 400. A `null` value for a known field also needs a defined result.
  Mitigation: reject all with 400 using a single error shape.
- L2. Length counting. "255 characters" should mean Unicode code points after trim, matching the client `maxlength`. If a SQL CHECK constraint is added, it must use `length()` consistently, which counts characters in SQLite.
- L3. Unknown or non-integer `<id>` returns 404. Negative, zero and overflow-sized values should also return 404 without a 500. Add a test for a very large integer.
- L4. Response shape is unspecified. Define the task object as `{id, description, completed (boolean), created_at}`. The DB stores 0/1, so the repository must convert to a JSON boolean.
- L5. Delete is immediate with no undo (A4). This is an accepted limitation and is documented. No change needed.
- L6. Accessibility and browser targets are best effort (Q6). This is acceptable and is recorded as a limitation. Add semantic labels and keyboard-operable controls to the implementation plan.
- L7. Port conflict or an unwritable data directory at startup. Failure behavior is not described. Recommend a clear startup error message.
- L8. Dependencies should be pinned in `requirements.txt` (Flask and pytest versions). The file name also resembles the story's `requirements.md`, so the README should state the difference. Minor.

## 4. Decisions on architect's open decisions (recommendations; not human approvals)

| ID | Recommendation | Rationale |
|---|---|---|
| OD1 | Accept Python 3.10+, Flask, SQLite (stdlib `sqlite3`) and vanilla JS as the working stack. Mark it an unconfirmed assumption (Q1) and keep it replaceable. | The story names no stack (A8). It is minimal and meets the local setup need. Components remain valid if the stack changes. |
| OD2 | Reject unknown PATCH fields with 400. | Strictness catches client bugs and avoids silent data loss. It is simple to test. |
| OD3 | Include `created_at` (UTC ISO-8601). | A1 permits it. It is cheap and gives a deterministic secondary ordering and future flexibility. Ordering stays by `id`. |
| OD4 | Do not require an automated browser test. Add a manual refresh check (T6) recorded as MANUAL in `verification.md`. An optional automated test may be added only if it adds no heavy dependencies. | Keeps scope minimal. The server-side persistence test across a new app instance covers the data path. Verification must not report the manual check as automated or passed unless it actually ran. |
| OD5 | Q2..Q9 stay unconfirmed assumptions as set out in architecture section 2. They are not blockers (requirements section 10). | The assumptions are reasonable and are labeled. Q8 (page ID inferred) concerns traceability only. |

## 5. Assessment by area

- Completeness: good. Every requirement and derived test maps to a component or test.
- Component boundaries: good. Validation and SQL are each in one place. The layout is non-binding.
- Data flow: consistent. The server is the source of truth, and the UI keeps prior state on failure.
- Security and trust boundaries: adequate for a local no-auth app. Parameterised SQL, `textContent` and localhost binding are in place. M1..M4 close the remaining gaps.
- Failure behavior and reliability: good coverage. M5 adds the connection details. Last-write-wins and no migrations are accepted limitations.
- Testability: good. The app factory takes a DB path and tests use a temporary DB. M4 and M6 add tests.
- Scope: appropriate. No out-of-scope features were added. `created_at` is minor and optional.

## 6. Recommended architecture revisions (non-blocking, for the next revision or the planner)

1. State debug off by default (M1).
2. Add Host header allowlist (M2).
3. Require strict `application/json` and no forced parsing (M3).
4. Add an automated no-`innerHTML` check (M4).
5. Specify SQLite timeout, transaction handling and the 500 test (M5).
6. Specify strict type checks and the extra validation tests (M6, L1, L3).
7. Define the task JSON shape (L4).

## 7. Limits of this review

- Based on documents only. No code was reviewed or run.
- Requirements are unapproved. All assumptions remain unconfirmed.

RESULT: PASS
