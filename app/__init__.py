"""Flask application factory."""
import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from . import repository
from .config import load_config
from .routes import bp


logger = logging.getLogger(__name__)

_MESSAGES = {
    400: "Bad request.",
    404: "Not found.",
    405: "Method not allowed.",
    413: "Request body too large.",
    415: "Content-Type must be application/json.",
}


def _register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http(exc):
        code = exc.code or 500
        message = _MESSAGES.get(code, "Request failed." if code < 500 else "Internal server error.")
        response = jsonify({"error": message})
        response.status_code = code
        if code == 405 and exc.valid_methods:
            response.headers["Allow"] = ", ".join(exc.valid_methods)
        return response

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        # Details go to the server log only; the body stays generic (M5).
        logger.error("Unhandled error", exc_info=exc)
        response = jsonify({"error": "Internal server error."})
        response.status_code = 500
        return response


ALLOWED_HOSTNAMES = ("127.0.0.1", "localhost")


def _register_security(app):
    """Host allowlist against DNS rebinding (M2) and nosniff header."""

    @app.before_request
    def check_host():
        host = (request.host or "").strip().lower()
        name, sep, port = host.rpartition(":")
        if not sep or not port.isdigit():
            name, port = host, ""
        # Port may be omitted (e.g. test client) or must equal the configured port.
        if name in ALLOWED_HOSTNAMES and port in ("", str(app.config["PORT"])):
            return None
        response = jsonify({"error": "Host not allowed."})
        response.status_code = 400
        return response

    @app.after_request
    def add_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response


def create_app(db_path=None, testing=False):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.update(load_config(db_path=db_path, testing=testing))
    repository.init_db(app.config["DATABASE"])
    app.register_blueprint(bp)
    _register_error_handlers(app)
    _register_security(app)
    return app
