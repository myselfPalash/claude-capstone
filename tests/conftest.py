"""Shared pytest fixtures: app on a temp DB and a test client."""
import pytest

from app import create_app


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def app(db_path):
    return create_app(db_path=db_path, testing=True)


@pytest.fixture
def client(app):
    return app.test_client()
