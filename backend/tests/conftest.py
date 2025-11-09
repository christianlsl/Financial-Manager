import os
import tempfile
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.db import Base, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def temp_db() -> str:
    fd, path = tempfile.mkstemp()
    os.close(fd)
    original = config.settings.SQLITE_DB_PATH
    config.settings.SQLITE_DB_PATH = path
    try:
        yield path
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        config.settings.SQLITE_DB_PATH = original


@pytest.fixture()
def client(temp_db: str) -> TestClient:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client: TestClient) -> Callable[[str, str], Dict[str, str]]:
    def _create(email: str = "user@example.com", password: str = "1234") -> Dict[str, str]:
        register_resp = client.post("/auth/register", json={"email": email, "password": password})
        if register_resp.status_code not in (200, 400):
            pytest.fail(f"Unexpected register status {register_resp.status_code}: {register_resp.text}")
        if register_resp.status_code == 400:
            detail = register_resp.json().get("detail")
            if detail != "Email already registered":
                pytest.fail(f"Unexpected register error: {detail}")
        login_resp = client.post("/auth/login", json={"email": email, "password": password})
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _create
