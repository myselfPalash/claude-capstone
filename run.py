"""Entry point: python run.py. Local development server (see README)."""
import socket
import sqlite3
import sys

from app import create_app
from app.config import load_config


def _fail(message):
    print("Error: " + message, file=sys.stderr)
    return 1


def _port_available(host, port):
    """Probe without SO_REUSEADDR so a port already in use is detected on every OS."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        family, socktype, proto, _, addr = infos[0]
        with socket.socket(family, socktype, proto) as probe:
            probe.bind(addr)
    except OSError:
        return False
    return True


def main():
    try:
        config = load_config()
    except ValueError as exc:
        return _fail(str(exc))

    try:
        app = create_app()
    except sqlite3.DatabaseError as exc:
        # Includes corrupt/non-database files. No auto-repair.
        return _fail("cannot open database at %s (%s). Fix or remove the file manually." % (config["DATABASE"], exc))
    except OSError as exc:
        return _fail("data directory/database not usable at %s (%s)." % (config["DATABASE"], exc))

    host, port = config["HOST"], config["PORT"]
    if not _port_available(host, port):
        return _fail("cannot listen on %s:%s (port in use or not permitted). Set TODO_PORT to a free port." % (host, port))
    try:
        app.run(host=host, port=port, debug=config["DEBUG"])
    except OSError as exc:
        return _fail("cannot listen on %s:%s (%s). Is the port already in use? Set TODO_PORT." % (host, port, exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
