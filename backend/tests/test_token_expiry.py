import time
from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core import config
from app.db import get_db
from app.models.user import User
from app.core.security import get_password_hash


client = TestClient(app)


def _ensure_user(email: str, password: str):
    # Direct DB access to create a user quickly without hitting register route multiple times
    with next(get_db()) as db:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return existing
        u = User(email=email, hashed_password=get_password_hash(password))
        db.add(u)
        db.commit()
        db.refresh(u)
        return u


def test_expired_token_rejected():
    email = "expire@example.com"
    password = "1234"
    _ensure_user(email, password)

    # Create a token that expires almost immediately
    token = create_access_token(subject=email, expires_delta=timedelta(seconds=1))
    time.sleep(2)  # ensure expiry passed

    r = client.get("/companies/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    data = r.json()
    # Detail should show Token expired from our explicit handler
    assert data.get("detail") == "Token expired"