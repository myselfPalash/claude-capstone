"""Basic tests for list and create routes (T-07). Full API tests are in T-11."""


def test_list_empty(client):
    r = client.get("/api/tasks")
    assert r.status_code == 200
    assert r.get_json() == []


def test_create_then_list(client):
    r = client.post("/api/tasks", json={"description": "  buy milk "})
    assert r.status_code == 201
    body = r.get_json()
    assert body["description"] == "buy milk"
    assert body["completed"] is False
    assert client.get("/api/tasks").get_json() == [body]


def test_create_invalid_returns_400(client):
    r = client.post("/api/tasks", json={"description": "   "})
    assert r.status_code == 400
    assert isinstance(r.get_json()["error"], str)


def test_create_malformed_json_returns_400(client):
    r = client.post("/api/tasks", data="{bad", content_type="application/json")
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_create_wrong_content_type_returns_415(client):
    r = client.post("/api/tasks", data='{"description": "x"}', content_type="text/plain")
    assert r.status_code == 415
    assert client.get("/api/tasks").get_json() == []


def test_create_no_content_type_returns_415(client):
    assert client.post("/api/tasks", data='{"description": "x"}').status_code == 415


def test_create_non_object_returns_400(client):
    assert client.post("/api/tasks", json=["a"]).status_code == 400
    assert client.post("/api/tasks", data="null", content_type="application/json").status_code == 400
