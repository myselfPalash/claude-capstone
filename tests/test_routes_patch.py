"""Focused tests for PATCH /api/tasks/<id> (T-08). Full API tests are in T-11."""
import pytest


@pytest.fixture
def task(client):
    return client.post("/api/tasks", json={"description": "orig"}).get_json()


def url(t):
    return "/api/tasks/%d" % t["id"]


def test_edit_description(client, task):
    r = client.patch(url(task), json={"description": "  new text "})
    assert r.status_code == 200
    body = r.get_json()
    assert body["description"] == "new text"
    assert body["completed"] is False
    assert client.get("/api/tasks").get_json() == [body]


def test_toggle_both_ways(client, task):
    r = client.patch(url(task), json={"completed": True})
    assert r.status_code == 200 and r.get_json()["completed"] is True
    assert r.get_json()["description"] == "orig"
    r = client.patch(url(task), json={"completed": False})
    assert r.get_json()["completed"] is False


def test_edit_both_fields(client, task):
    r = client.patch(url(task), json={"description": "x", "completed": True})
    assert r.get_json()["description"] == "x"
    assert r.get_json()["completed"] is True


def test_missing_id_404_json(client):
    r = client.patch("/api/tasks/999", json={"completed": True})
    assert r.status_code == 404
    assert isinstance(r.get_json()["error"], str)


@pytest.mark.parametrize("body", [
    {},
    {"foo": 1},
    {"description": "ok", "foo": 1},
    {"description": None},
    {"completed": None},
    {"description": ""},
    {"description": "   "},
    {"description": 5},
    {"completed": 1},
    {"completed": "true"},
    [],
    "str",
])
def test_invalid_payload_400(client, task, body):
    r = client.patch(url(task), json=body)
    assert r.status_code == 400
    assert isinstance(r.get_json()["error"], str)
    assert client.get("/api/tasks").get_json()[0]["description"] == "orig"


def test_malformed_json_400(client, task):
    r = client.patch(url(task), data="{bad", content_type="application/json")
    assert r.status_code == 400


@pytest.mark.parametrize("ctype", ["text/plain", "application/x-www-form-urlencoded", "application/ld+json"])
def test_wrong_content_type_415(client, task, ctype):
    r = client.patch(url(task), data='{"completed": true}', content_type=ctype)
    assert r.status_code == 415
    assert "error" in r.get_json()


def test_no_content_type_415(client, task):
    assert client.patch(url(task), data='{"completed": true}').status_code == 415
