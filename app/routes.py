"""HTTP API routes: list and create tasks, and serve the frontend page."""
from flask import Blueprint, current_app, jsonify, request, send_from_directory

from . import repository
from .validation import ValidationError, validate_create_payload, validate_patch_payload

bp = Blueprint("api", __name__)


def _error(message, status):
    return jsonify({"error": message}), status


def _read_json_object():
    """Parse the body as JSON without force=True.

    Returns (payload, None) or (None, error_response). Strict content type
    (415) is checked before parsing; malformed JSON gives 400.
    """
    if not request.is_json or request.mimetype != "application/json":
        return None, _error("Content-Type must be application/json.", 415)
    payload = request.get_json(silent=True)
    if payload is None and request.get_data(cache=True).strip() != b"null":
        return None, _error("Request body is not valid JSON.", 400)
    return payload, None


@bp.get("/")
def index():
    return send_from_directory(current_app.static_folder, "index.html")


@bp.get("/api/tasks")
def list_tasks():
    return jsonify(repository.list_tasks(current_app.config["DATABASE"])), 200


@bp.post("/api/tasks")
def create_task():
    payload, err = _read_json_object()
    if err:
        return err
    try:
        clean = validate_create_payload(payload)
    except ValidationError as exc:
        return _error(str(exc), 400)
    task = repository.create_task(current_app.config["DATABASE"], clean["description"])
    return jsonify(task), 201


@bp.patch("/api/tasks/<task_id>")
def update_task(task_id):
    parsed = _parse_id(task_id)
    if parsed is None:
        return _error("Task not found.", 404)
    payload, err = _read_json_object()
    if err:
        return err
    try:
        clean = validate_patch_payload(payload)
    except ValidationError as exc:
        return _error(str(exc), 400)
    task = repository.update_task(
        current_app.config["DATABASE"],
        parsed,
        description=clean.get("description"),
        completed=clean.get("completed"),
    )
    if task is None:
        return _error("Task not found.", 404)
    return jsonify(task), 200


def _parse_id(raw):
    """Parse a positive decimal integer id; return None if it is not one."""
    if len(raw) > 19 or not raw.isascii() or not raw.isdigit():
        return None
    value = int(raw)
    return value if value > 0 else None


@bp.delete("/api/tasks/<task_id>")
def delete_task(task_id):
    parsed = _parse_id(task_id)
    if parsed is None:
        return _error("Task not found.", 404)
    if not repository.delete_task(current_app.config["DATABASE"], parsed):
        return _error("Task not found.", 404)
    return "", 204
