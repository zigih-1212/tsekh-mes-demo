import os
import tempfile

# DATABASE_URL переопределяем ДО импорта приложения — движок создаётся при импорте db.py
_tmpdir = tempfile.mkdtemp(prefix="tsekh-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ.setdefault("SECRET_KEY", "test-secret")

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine, SessionLocal
from app.main import app
from app.seed import seed_if_empty


@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    with TestClient(app) as c:
        yield c


def _login(client: TestClient, email: str, password: str) -> dict:
    r = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin_headers(client):
    return _login(client, "admin@artraid.demo", "admin123")


@pytest.fixture(scope="session")
def operator_headers(client):
    return _login(client, "op1@artraid.demo", "demo1234")


@pytest.fixture(scope="session")
def operator2_headers(client):
    return _login(client, "op2@artraid.demo", "demo1234")


@pytest.fixture(scope="session")
def foreman_headers(client):
    return _login(client, "foreman@artraid.demo", "demo1234")


@pytest.fixture(scope="session")
def store_headers(client):
    return _login(client, "store@artraid.demo", "demo1234")
