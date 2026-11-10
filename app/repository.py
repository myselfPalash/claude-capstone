"""SQLite data access. All SQL is parameterised; one connection per operation."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_TIMEOUT_SECONDS = 5.0
_MAX_SQLITE_INT = 2**63 - 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
)
"""

_COLUMNS = "id, description, completed, created_at"


def _connect(db_path):
    conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _transaction(db_path):
    """Open a connection, commit on success, roll back on any error, always close."""
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def _to_task(row):
    return {
        "id": row["id"],
        "description": row["description"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
    }


def _valid_id(task_id):
    return isinstance(task_id, int) and not isinstance(task_id, bool) and 1 <= task_id <= _MAX_SQLITE_INT


def init_db(db_path):
    """Create the data directory (if needed) and the schema if absent."""
    db_path = str(db_path)
    directory = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(directory, exist_ok=True)
    with _transaction(db_path) as conn:
        conn.execute(SCHEMA)


def create_task(db_path, description):
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _transaction(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO tasks (description, completed, created_at) VALUES (?, 0, ?)",
            (description, created_at),
        )
        row = conn.execute(
            "SELECT " + _COLUMNS + " FROM tasks WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _to_task(row)


def list_tasks(db_path):
    with _transaction(db_path) as conn:
        rows = conn.execute("SELECT " + _COLUMNS + " FROM tasks ORDER BY id").fetchall()
        return [_to_task(r) for r in rows]


def get_task(db_path, task_id):
    """Return the task dict, or None if not found (including out-of-range ids)."""
    if not _valid_id(task_id):
        return None
    with _transaction(db_path) as conn:
        row = conn.execute(
            "SELECT " + _COLUMNS + " FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return _to_task(row) if row else None


def update_task(db_path, task_id, description=None, completed=None):
    """Update given fields (None = leave unchanged). Return updated task or None."""
    if not _valid_id(task_id):
        return None
    with _transaction(db_path) as conn:
        row = conn.execute(
            "SELECT " + _COLUMNS + " FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        new_desc = row["description"] if description is None else description
        new_completed = row["completed"] if completed is None else (1 if completed else 0)
        conn.execute(
            "UPDATE tasks SET description = ?, completed = ? WHERE id = ?",
            (new_desc, new_completed, task_id),
        )
        row = conn.execute(
            "SELECT " + _COLUMNS + " FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return _to_task(row)


def delete_task(db_path, task_id):
    """Return True if a row was deleted, False if not found."""
    if not _valid_id(task_id):
        return False
    with _transaction(db_path) as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cur.rowcount > 0
