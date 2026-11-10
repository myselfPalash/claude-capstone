# claude-capstone

## Overview

A small single-user to-do web application. A browser page lets you add, view, complete/uncomplete, edit and delete tasks. Tasks are stored in a local SQLite database and served by a Flask JSON API.

Stack (an unconfirmed assumption recorded in `architecture.md`): Python 3.10+, Flask, SQLite (standard library `sqlite3`), plain HTML/CSS/JavaScript frontend served from `app/static/`.

## Setup

Prerequisite: Python 3.10 or newer.

Create and activate a virtual environment, then install dependencies.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

POSIX shell:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Note: `requirements.txt` is the pinned Python dependency list (Flask, pytest). It is unrelated to `requirements.md`, which holds the story requirements.

## Run

```sh
python run.py
```

Then open http://127.0.0.1:5000/ in a browser (default host and port).

## Environment variables

All are optional.

| Variable | Default | Meaning |
|----------|---------|---------|
| `TODO_DB_PATH` | `data/todo.db` under the project root | SQLite database file path |
| `TODO_HOST` | `127.0.0.1` | Interface to listen on |
| `TODO_PORT` | `5000` | Port (integer 1-65535) |
| `TODO_DEBUG` | off | Flask debug mode; enabled only if set to `1`, `true`, `yes` or `on` (case-insensitive) |

## Tests

```sh
pytest
```

Browser behaviour (refresh persistence, keyboard/focus, rendering) is not covered by automated tests; see the MANUAL checklist in [docs/manual-checks.md](docs/manual-checks.md).

## API summary

| Method and path | Purpose | Success |
|-----------------|---------|---------|
| `GET /` | Frontend page | 200 |
| `GET /api/tasks` | List tasks | 200 |
| `POST /api/tasks` | Create task (JSON `description`) | 201 |
| `PATCH /api/tasks/<id>` | Update `description` and/or `completed` | 200 |
| `DELETE /api/tasks/<id>` | Delete task | 204 |

Request bodies must use `Content-Type: application/json` (otherwise 415). Invalid input returns 400 and an unknown or malformed id returns 404, with a JSON body of the form `{"error": "..."}`. Descriptions are trimmed and limited to 255 characters; request bodies are limited to about 10 KB.

## Security notes

- Intended for localhost use only. The default bind address is `127.0.0.1`. Do not expose this application publicly.
- Requests are accepted only when the `Host` header is `127.0.0.1` or `localhost` (with the configured port or no port), as a defence against DNS rebinding. Residual risk remains and this is not a substitute for real access control.
- There is no authentication by design (story scope). Anyone who can reach the server can read and change all tasks.
- Debug mode is off by default; enable it only with `TODO_DEBUG` on a trusted local machine.
- `python run.py` uses the Flask development server, not a production server.

## Startup errors

If configuration is invalid (for example a bad `TODO_PORT`), the database cannot be opened or is corrupt, the data directory is unusable, or the port is in use, `run.py` prints a single line starting with `Error:` to stderr and exits with status 1. A corrupt database is not repaired automatically.

## Limitations and assumptions

- The stack and design decisions are unconfirmed assumptions, not approved by a human.
- There is one global task list shared by everyone who can reach the server.
- No authentication or user accounts.
- Local development server only; no deployment setup.
- No pagination or schema migrations.
- Concurrent edits are last-write-wins; delete has no undo.
- Persistence across a browser refresh has not been verified in a browser; check it manually.
