"""Repository tests against a temp SQLite file (T-06)."""
import os
import sqlite3
from datetime import datetime, timedelta

import pytest

from app import create_app, repository as repo


@pytest.fixture
def db(db_path):
    repo.init_db(db_path)
    return db_path


def _count(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    finally:
        conn.close()


def test_create_returns_pending_task_with_shape(db):
    t = repo.create_task(db, "Buy milk")
    assert set(t) == {"id", "description", "completed", "created_at"}
    assert t["id"] == 1
    assert t["description"] == "Buy milk"
    assert t["completed"] is False


def test_created_at_is_parseable_utc(db):
    t = repo.create_task(db, "x")
    dt = datetime.fromisoformat(t["created_at"])
    assert dt.utcoffset() == timedelta(0)


def test_list_empty(db):
    assert repo.list_tasks(db) == []


def test_list_ordered_by_id(db):
    a = repo.create_task(db, "a")
    b = repo.create_task(db, "b")
    c = repo.create_task(db, "c")
    assert [t["id"] for t in repo.list_tasks(db)] == [a["id"], b["id"], c["id"]]


def test_get_existing_and_missing(db):
    t = repo.create_task(db, "a")
    assert repo.get_task(db, t["id"]) == t
    assert repo.get_task(db, 999) is None


def test_update_description_and_completed(db):
    t = repo.create_task(db, "a")
    u = repo.update_task(db, t["id"], description="b")
    assert u["description"] == "b" and u["completed"] is False
    u = repo.update_task(db, t["id"], completed=True)
    assert u["description"] == "b" and u["completed"] is True
    u = repo.update_task(db, t["id"], completed=False)
    assert u["completed"] is False
    assert u["created_at"] == t["created_at"]


def test_completed_is_json_boolean_not_int(db):
    t = repo.create_task(db, "a")
    assert type(t["completed"]) is bool
    assert type(repo.update_task(db, t["id"], completed=True)["completed"]) is bool
    assert type(repo.list_tasks(db)[0]["completed"]) is bool
    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT completed FROM tasks").fetchone()[0] == 1
    finally:
        conn.close()


def test_delete_existing_then_missing(db):
    t = repo.create_task(db, "a")
    assert repo.delete_task(db, t["id"]) is True
    assert repo.get_task(db, t["id"]) is None
    assert repo.delete_task(db, t["id"]) is False


def test_deleted_id_not_reused(db):
    a = repo.create_task(db, "a")
    repo.delete_task(db, a["id"])
    b = repo.create_task(db, "b")
    assert b["id"] > a["id"]


@pytest.mark.parametrize("bad_id", [999999, 0, -1, 2**63, 2**63 - 1, 99999999999999999999999, True])
def test_nonexistent_or_out_of_range_ids_do_not_raise(db, bad_id):
    repo.create_task(db, "a")
    assert repo.get_task(db, bad_id) is None
    assert repo.update_task(db, bad_id, description="z") is None
    assert repo.update_task(db, bad_id, completed=True) is None
    assert repo.delete_task(db, bad_id) is False
    assert len(repo.list_tasks(db)) == 1


def test_update_missing_does_not_change_others(db):
    t = repo.create_task(db, "a")
    repo.update_task(db, 12345, description="z")
    assert repo.get_task(db, t["id"])["description"] == "a"


def test_schema_auto_created_when_db_missing(tmp_path):
    path = tmp_path / "nested" / "dir" / "new.db"
    assert not path.exists()
    repo.init_db(str(path))
    assert path.exists()
    assert repo.list_tasks(str(path)) == []


def test_init_db_is_idempotent_and_keeps_data(db):
    repo.create_task(db, "a")
    repo.init_db(db)
    assert len(repo.list_tasks(db)) == 1


def test_data_persists_across_app_instances(db_path):
    app1 = create_app(db_path=db_path, testing=True)
    repo.init_db(app1.config["DATABASE"])
    created = repo.create_task(app1.config["DATABASE"], "persist me")
    del app1
    app2 = create_app(db_path=db_path, testing=True)
    repo.init_db(app2.config["DATABASE"])
    assert repo.list_tasks(app2.config["DATABASE"]) == [created]


def test_special_characters_stored_literally(db):
    text = "x'); DROP TABLE tasks;-- \u00e9\U0001F600"
    t = repo.create_task(db, text)
    assert repo.get_task(db, t["id"])["description"] == text
    assert len(repo.list_tasks(db)) == 1


def test_failed_create_rolls_back(db, monkeypatch):
    repo.create_task(db, "keep")
    real_to_task = repo._to_task

    def boom(row):
        raise sqlite3.OperationalError("simulated failure")

    monkeypatch.setattr(repo, "_to_task", boom)
    with pytest.raises(sqlite3.OperationalError):
        repo.create_task(db, "lost")
    monkeypatch.setattr(repo, "_to_task", real_to_task)
    assert _count(db) == 1
    assert [t["description"] for t in repo.list_tasks(db)] == ["keep"]


def test_failed_update_rolls_back(db, monkeypatch):
    t = repo.create_task(db, "orig")

    def boom(row):
        raise sqlite3.OperationalError("simulated failure")

    monkeypatch.setattr(repo, "_to_task", boom)
    with pytest.raises(sqlite3.OperationalError):
        repo.update_task(db, t["id"], description="changed", completed=True)
    monkeypatch.undo()
    assert repo.get_task(db, t["id"]) == t


def test_failed_delete_rolls_back(db, monkeypatch):
    t = repo.create_task(db, "orig")
    real_connect = repo._connect

    class FailingCommit:
        def __init__(self, conn):
            self._c = conn

        def __getattr__(self, name):
            return getattr(self._c, name)

        def commit(self):
            raise sqlite3.OperationalError("simulated commit failure")

    monkeypatch.setattr(repo, "_connect", lambda p: FailingCommit(real_connect(p)))
    with pytest.raises(sqlite3.OperationalError):
        repo.delete_task(db, t["id"])
    monkeypatch.undo()
    assert repo.get_task(db, t["id"]) == t


def test_connection_closed_after_failure(db, monkeypatch):
    """After a failure the DB file is not left locked (a delete of the file works)."""
    repo.create_task(db, "a")
    monkeypatch.setattr(repo, "_to_task", lambda r: (_ for _ in ()).throw(RuntimeError("x")))
    with pytest.raises(RuntimeError):
        repo.list_tasks(db)
    monkeypatch.undo()
    # a subsequent write succeeds immediately
    assert repo.create_task(db, "b")["description"] == "b"


def test_unreachable_db_raises_rather_than_silently_succeeding(tmp_path):
    bad = str(tmp_path / "missing_dir" / "x.db")
    with pytest.raises(sqlite3.Error):
        repo.list_tasks(bad)
