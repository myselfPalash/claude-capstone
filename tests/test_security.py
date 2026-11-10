"""Security and edge-case tests (T-13): Host allowlist, content type, config, strict types."""
import json

import pytest

from app import create_app, repository
from app.config import load_config


# --- Host allowlist (M2) ---------------------------------------------------

@pytest.mark.parametrize("host", [
    "127.0.0.1", "localhost", "127.0.0.1:5000", "localhost:5000", "LOCALHOST:5000",
])
def test_allowed_hosts_accepted(client, host):
    r = client.get("/api/tasks", headers={"Host": host})
    assert r.status_code == 200


@pytest.mark.parametrize("host", [
    "evil.com", "localhost.evil.com", "localhost.evil.com:5000", "127.0.0.1.evil.com",
    "evil.com:5000", "localhost:6000", "127.0.0.1:1", "0.0.0.0:5000", "[::1]:5000",
])
def test_bad_hosts_rejected(client, host):
    r = client.get("/api/tasks", headers={"Host": host})
    assert r.status_code == 400
    assert r.get_json() == {"error": "Host not allowed."}


def test_bad_host_rejected_on_write_methods_and_nothing_stored(client):
    bad = {"Host": "evil.com"}
    assert client.post("/api/tasks", json={"description": "x"}, headers=bad).status_code == 400
    assert client.get("/api/tasks").get_json() == []
    assert client.delete("/api/tasks/1", headers=bad).status_code == 400
    assert client.patch("/api/tasks/1", json={"completed": True}, headers=bad).status_code == 400


def test_bad_host_rejected_for_static_and_index(client):
    assert client.get("/", headers={"Host": "evil.com"}).status_code == 400
    assert client.get("/static/app.js", headers={"Host": "evil.com"}).status_code == 400


def test_host_port_follows_configured_port(db_path, monkeypatch):
    monkeypatch.setenv("TODO_PORT", "8123")
    app = create_app(db_path=db_path, testing=True)
    c = app.test_client()
    assert c.get("/api/tasks", headers={"Host": "localhost:8123"}).status_code == 200
    assert c.get("/api/tasks", headers={"Host": "localhost:5000"}).status_code == 400


def test_nosniff_header_on_success_and_error(client):
    assert client.get("/api/tasks").headers["X-Content-Type-Options"] == "nosniff"
    assert client.get("/api/nope").headers["X-Content-Type-Options"] == "nosniff"
    r = client.get("/api/tasks", headers={"Host": "evil.com"})
    assert r.headers["X-Content-Type-Options"] == "nosniff"


# --- Content type / body (M3) ----------------------------------------------

def test_post_and_patch_non_json_content_type_415(client):
    t = client.post("/api/tasks", json={"description": "x"}).get_json()
    body = json.dumps({"description": "y"})
    for ctype in ("text/plain", "application/x-www-form-urlencoded", "text/html"):
        r = client.post("/api/tasks", data=body, content_type=ctype)
        assert r.status_code == 415
        r = client.patch(f"/api/tasks/{t['id']}", data=body, content_type=ctype)
        assert r.status_code == 415
    tasks = client.get("/api/tasks").get_json()
    assert len(tasks) == 1 and tasks[0]["description"] == "x"


def test_missing_content_type_with_body_415(client):
    r = client.post("/api/tasks", data=json.dumps({"description": "x"}))
    assert r.status_code == 415
    assert client.get("/api/tasks").get_json() == []


def test_malformed_json_400_on_post_and_patch(client):
    t = client.post("/api/tasks", json={"description": "x"}).get_json()
    for method, url in (("post", "/api/tasks"), ("patch", f"/api/tasks/{t['id']}")):
        r = getattr(client, method)(url, data="{not json", content_type="application/json")
        assert r.status_code == 400
        assert list(r.get_json()) == ["error"]


def test_oversized_body_413_on_patch_and_nothing_changed(client):
    t = client.post("/api/tasks", json={"description": "x"}).get_json()
    big = json.dumps({"description": "a" * 20000})
    r = client.patch(f"/api/tasks/{t['id']}", data=big, content_type="application/json")
    assert r.status_code == 413
    assert client.get("/api/tasks").get_json()[0]["description"] == "x"


def test_no_cors_headers_on_any_method(client):
    origin = {"Origin": "http://evil.com"}
    t = client.post("/api/tasks", json={"description": "x"}, headers=origin)
    p = client.patch(f"/api/tasks/{t.get_json()['id']}", json={"completed": True}, headers=origin)
    o = client.options("/api/tasks", headers=origin)
    g = client.get("/api/tasks", headers=origin)
    for r in (t, p, o, g):
        assert not [h for h in r.headers.keys() if h.lower().startswith("access-control-")]


# --- Strict types (M6) -----------------------------------------------------

@pytest.mark.parametrize("payload", [
    {"description": 123}, {"description": None}, {"description": ["a"]},
    {"description": {"a": 1}}, {"description": True}, {"description": "   "},
    {"description": "a" * 256}, {}, [], "text", 5,
])
def test_post_rejects_invalid_payloads(client, payload):
    r = client.post("/api/tasks", json=payload)
    assert r.status_code == 400
    assert client.get("/api/tasks").get_json() == []


@pytest.mark.parametrize("value", [1, 0, "true", "false", None, "yes", [], {}])
def test_patch_completed_must_be_real_boolean(client, value):
    t = client.post("/api/tasks", json={"description": "x"}).get_json()
    r = client.patch(f"/api/tasks/{t['id']}", json={"completed": value})
    assert r.status_code == 400
    assert client.get("/api/tasks").get_json()[0]["completed"] is False


def test_patch_unknown_field_and_empty_rejected(client):
    t = client.post("/api/tasks", json={"description": "x"}).get_json()
    for payload in ({}, {"id": 5}, {"completed": True, "extra": 1}, {"description": None}):
        assert client.patch(f"/api/tasks/{t['id']}", json=payload).status_code == 400


def test_description_length_counts_code_points(client):
    assert client.post("/api/tasks", json={"description": "\U0001F600" * 255}).status_code == 201
    assert client.post("/api/tasks", json={"description": "\U0001F600" * 256}).status_code == 400


def test_sql_injection_text_stored_literally(client):
    text = "x'); DROP TABLE tasks;--"
    assert client.post("/api/tasks", json={"description": text}).status_code == 201
    assert client.get("/api/tasks").get_json()[0]["description"] == text


# --- Config (M1) -----------------------------------------------------------

@pytest.fixture
def clean_env(monkeypatch):
    for name in ("TODO_DEBUG", "TODO_HOST", "TODO_PORT", "TODO_DB_PATH"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_default_config_debug_off_and_loopback(clean_env):
    cfg = load_config()
    assert cfg["DEBUG"] is False
    assert cfg["HOST"] == "127.0.0.1"
    assert cfg["PORT"] == 5000


def test_debug_only_on_explicit_flag(clean_env):
    for v in ("1", "true", "TRUE", "yes", "on"):
        clean_env.setenv("TODO_DEBUG", v)
        assert load_config()["DEBUG"] is True
    for v in ("", "0", "false", "no", "off", "banana"):
        clean_env.setenv("TODO_DEBUG", v)
        assert load_config()["DEBUG"] is False


def test_testing_mode_forces_debug_off(clean_env):
    clean_env.setenv("TODO_DEBUG", "1")
    assert load_config(testing=True)["DEBUG"] is False


def test_env_overrides_host_port_db(clean_env, tmp_path):
    clean_env.setenv("TODO_HOST", "localhost")
    clean_env.setenv("TODO_PORT", "8080")
    clean_env.setenv("TODO_DB_PATH", str(tmp_path / "e.db"))
    cfg = load_config()
    assert (cfg["HOST"], cfg["PORT"], cfg["DATABASE"]) == ("localhost", 8080, str(tmp_path / "e.db"))
    assert load_config(db_path="explicit.db")["DATABASE"] == "explicit.db"


@pytest.mark.parametrize("bad", ["abc", "5.5", "0", "-1", "65536", "99999"])
def test_bad_port_raises_value_error(clean_env, bad):
    clean_env.setenv("TODO_PORT", bad)
    with pytest.raises(ValueError, match="TODO_PORT"):
        load_config()


def test_max_content_length_set(app):
    assert 0 < app.config["MAX_CONTENT_LENGTH"] <= 16 * 1024


# --- Generic 500 on write path (M5) ----------------------------------------

def test_500_generic_on_post(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("secret path /srv/db.sqlite")

    monkeypatch.setattr(repository, "create_task", boom)
    r = client.post("/api/tasks", json={"description": "x"})
    assert r.status_code == 500
    assert r.get_json() == {"error": "Internal server error."}
    assert "secret" not in r.get_data(as_text=True)
