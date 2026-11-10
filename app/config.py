"""Application configuration read from environment variables. No secrets."""
import os
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
MAX_CONTENT_LENGTH = 10 * 1024  # ~10 KB request body limit

_BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(_BASE_DIR / "data" / "todo.db")

_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_flag(name):
    return os.environ.get(name, "").strip().lower() in _TRUE_VALUES


def _env_port():
    raw = os.environ.get("TODO_PORT", "").strip()
    if not raw:
        return DEFAULT_PORT
    try:
        port = int(raw)
    except ValueError:
        raise ValueError("TODO_PORT must be an integer")
    if not 1 <= port <= 65535:
        raise ValueError("TODO_PORT must be between 1 and 65535")
    return port


def load_config(db_path=None, testing=False):
    """Build the config dict. Debug is OFF unless TODO_DEBUG is explicitly truthy."""
    return {
        "DATABASE": db_path or os.environ.get("TODO_DB_PATH") or DEFAULT_DB_PATH,
        "HOST": os.environ.get("TODO_HOST", "").strip() or DEFAULT_HOST,
        "PORT": _env_port(),
        "DEBUG": False if testing else _env_flag("TODO_DEBUG"),
        "TESTING": bool(testing),
        "MAX_CONTENT_LENGTH": MAX_CONTENT_LENGTH,
    }
