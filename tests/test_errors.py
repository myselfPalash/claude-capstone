"""Tests for JSON error handlers (T-10)."""
import json

from app import repository


def _is_generic_json(resp, status):
    assert resp.status_code == status
    assert resp.mimetype == "application/json"
    body = resp.get_json()
    assert list(body) == ["error"] and isinstance(body["error"], str)
    return body


def test_404_unknown_path_json(client):
    _is_generic_json(client.get("/api/nope"), 404)


def test_404_patch_bad_ids_json(client):
    for bad in ("abc", "0", "-1", "1.5"):
        _is_generic_json(client.patch(f"/api/tasks/{bad}", json={"completed": True}), 404)


def test_404_patch_missing_id_json(client):
    _is_generic_json(client.patch("/api/tasks/999", json={"completed": True}), 404)


def test_patch_valid_id_still_works(client):
    t = client.post("/api/tasks", json={"description": "x"}).get_json()
    r = client.patch(f"/api/tasks/{t['id']}", json={"completed": True})
    assert r.status_code == 200 and r.get_json()["completed"] is True


def test_405_json_with_allow(client):
    r = client.put("/api/tasks")
    _is_generic_json(r, 405)
    assert "GET" in r.headers["Allow"]


def test_400_malformed_json(client):
    r = client.post("/api/tasks", data="{bad", content_type="application/json")
    _is_generic_json(r, 400)


def test_415_wrong_content_type(client):
    r = client.post("/api/tasks", data=json.dumps({"description": "x"}), content_type="text/plain")
    _is_generic_json(r, 415)


def test_413_oversized_body(client):
    big = json.dumps({"description": "a" * 20000})
    r = client.post("/api/tasks", data=big, content_type="application/json")
    _is_generic_json(r, 413)


def test_500_generic_no_leak(app, client, monkeypatch, caplog):
    def boom(*a, **k):
        raise RuntimeError("SELECT * FROM tasks failed at /srv/secret/todo.db")

    monkeypatch.setattr(repository, "list_tasks", boom)
    r = client.get("/api/tasks")
    body = _is_generic_json(r, 500)
    text = r.get_data(as_text=True)
    for leak in ("SELECT", "secret", "todo.db", "Traceback", "RuntimeError", ".py"):
        assert leak not in text
    assert body["error"] == "Internal server error."
    assert "SELECT" in caplog.text  # details logged server-side only
