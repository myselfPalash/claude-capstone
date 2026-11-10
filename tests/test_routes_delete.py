"""Focused tests for DELETE /api/tasks/<id> (T-09). Full API tests are in T-11."""
import pytest


def test_delete_existing_returns_204_and_removes(client):
    a = client.post("/api/tasks", json={"description": "a"}).get_json()
    b = client.post("/api/tasks", json={"description": "b"}).get_json()
    r = client.delete("/api/tasks/%d" % a["id"])
    assert r.status_code == 204
    assert r.get_data() == b""
    assert client.get("/api/tasks").get_json() == [b]


def test_delete_twice_second_is_404(client):
    t = client.post("/api/tasks", json={"description": "a"}).get_json()
    assert client.delete("/api/tasks/%d" % t["id"]).status_code == 204
    r = client.delete("/api/tasks/%d" % t["id"])
    assert r.status_code == 404
    assert r.get_json() == {"error": "Task not found."}


@pytest.mark.parametrize(
    "bad", ["0", "-1", "abc", "99999999999999999999", "1.5", "+1", "%D9%A1", " 1"]
)
def test_delete_bad_ids_404_json_never_500(client, bad):
    keep = client.post("/api/tasks", json={"description": "keep"}).get_json()
    r = client.delete("/api/tasks/" + bad)
    assert r.status_code == 404
    assert r.get_json() == {"error": "Task not found."}
    assert client.get("/api/tasks").get_json() == [keep]


def test_delete_has_no_cors_headers(client):
    r = client.delete("/api/tasks/1")
    assert "Access-Control-Allow-Origin" not in r.headers


def test_delete_and_patch_huge_id_404_json_not_500(client):
    huge = "9" * 5000
    r = client.delete("/api/tasks/" + huge)
    assert r.status_code == 404
    assert r.get_json() == {"error": "Task not found."}
    r = client.patch("/api/tasks/" + huge, json={"description": "x"})
    assert r.status_code == 404
    assert r.get_json() == {"error": "Task not found."}
