"""Acceptance-mapped API tests (requirements checks T1..T7).

T6 is a server-side proxy only: a new app instance on the same DB file.
The real browser-refresh check (T6) is MANUAL and not covered here.
"""
from app import create_app

TASK_KEYS = {"id", "description", "completed", "created_at"}


def _add(client, text):
    return client.post("/api/tasks", json={"description": text})


def test_t1_add_returns_pending_task(client):
    resp = _add(client, "Buy milk")
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["description"] == "Buy milk"
    assert body["completed"] is False
    assert any(t["id"] == body["id"] for t in client.get("/api/tasks").get_json())


def test_t2_list_count_equals_n(client):
    for i in range(5):
        _add(client, f"task {i}")
    assert len(client.get("/api/tasks").get_json()) == 5


def test_t3_toggle_and_back_persists(client):
    tid = _add(client, "a").get_json()["id"]
    r = client.patch(f"/api/tasks/{tid}", json={"completed": True})
    assert r.status_code == 200 and r.get_json()["completed"] is True
    assert client.get("/api/tasks").get_json()[0]["completed"] is True
    r = client.patch(f"/api/tasks/{tid}", json={"completed": False})
    assert r.get_json()["completed"] is False
    assert client.get("/api/tasks").get_json()[0]["completed"] is False


def test_t4_edit_updates_list_and_stored_value(client, db_path):
    tid = _add(client, "old").get_json()["id"]
    r = client.patch(f"/api/tasks/{tid}", json={"description": "new"})
    assert r.status_code == 200 and r.get_json()["description"] == "new"
    assert client.get("/api/tasks").get_json()[0]["description"] == "new"
    other = create_app(db_path=db_path, testing=True).test_client()
    assert other.get("/api/tasks").get_json()[0]["description"] == "new"


def test_t5_delete_removes_from_list_and_storage(client, db_path):
    keep = _add(client, "keep").get_json()["id"]
    gone = _add(client, "gone").get_json()["id"]
    assert client.delete(f"/api/tasks/{gone}").status_code == 204
    ids = [t["id"] for t in client.get("/api/tasks").get_json()]
    assert ids == [keep]
    other = create_app(db_path=db_path, testing=True).test_client()
    assert [t["id"] for t in other.get("/api/tasks").get_json()] == [keep]
    assert client.delete(f"/api/tasks/{gone}").status_code == 404


def test_t6_server_side_persistence_new_app_instance(db_path):
    """Proxy for T6 only; browser refresh remains a manual check."""
    c1 = create_app(db_path=db_path, testing=True).test_client()
    a = _add(c1, "one").get_json()["id"]
    _add(c1, "two")
    c1.patch(f"/api/tasks/{a}", json={"completed": True})
    before = c1.get("/api/tasks").get_json()
    c2 = create_app(db_path=db_path, testing=True).test_client()
    after = c2.get("/api/tasks").get_json()
    assert after == before
    assert [t["completed"] for t in after] == [True, False]


def test_t7_all_operations_without_credentials(client):
    # No Authorization header, cookies or tokens are supplied anywhere.
    tid = _add(client, "x").get_json()["id"]
    assert client.get("/api/tasks").status_code == 200
    assert client.patch(f"/api/tasks/{tid}", json={"completed": True}).status_code == 200
    assert client.delete(f"/api/tasks/{tid}").status_code == 204


def test_end_to_end_crud_flow(client):
    assert client.get("/api/tasks").get_json() == []
    tid = _add(client, "flow").get_json()["id"]
    client.patch(f"/api/tasks/{tid}", json={"description": "flow2", "completed": True})
    listed = client.get("/api/tasks").get_json()
    assert len(listed) == 1
    assert (listed[0]["id"], listed[0]["description"], listed[0]["completed"]) == (
        tid, "flow2", True)
    client.delete(f"/api/tasks/{tid}")
    assert client.get("/api/tasks").get_json() == []


def test_task_json_shape_and_boolean_type(client):
    _add(client, "shape")
    task = client.get("/api/tasks").get_json()[0]
    assert set(task) == TASK_KEYS
    assert isinstance(task["id"], int) and not isinstance(task["id"], bool)
    assert isinstance(task["completed"], bool)


def test_list_ordered_by_id(client):
    ids = [_add(client, f"t{i}").get_json()["id"] for i in range(4)]
    assert [t["id"] for t in client.get("/api/tasks").get_json()] == sorted(ids)


def test_html_in_description_returned_verbatim_as_json(client):
    text = "<script>alert(1)</script> & <b>x</b>"
    resp = _add(client, text)
    assert resp.get_json()["description"] == text
    listed = client.get("/api/tasks")
    assert listed.mimetype == "application/json"
    assert listed.get_json()[0]["description"] == text


def test_invalid_ids_never_500(client):
    for bad in ("0", "-1", "abc", "99999999999999999999"):
        assert client.delete(f"/api/tasks/{bad}").status_code == 404
        assert client.patch(f"/api/tasks/{bad}", json={"completed": True}).status_code == 404
