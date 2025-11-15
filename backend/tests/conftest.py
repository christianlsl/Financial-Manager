import os
import tempfile
from typing import Callable, Dict, Generator

import pytest
from fastapi.testclient import TestClient
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from sqlalchemy import create_engine

from app.core import config
import app.db as app_db
from app.main import app
from app.models.customer import Customer
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def temp_db() -> Generator[str, None, None]:
    fd, path = tempfile.mkstemp()
    os.close(fd)
    original = config.settings.SQLITE_DB_PATH
    config.settings.SQLITE_DB_PATH = path
    original_engine = app_db.engine
    new_engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    app_db.engine = new_engine
    app_db.SessionLocal.configure(bind=new_engine)
    from app import main as app_main
    app_main.engine = new_engine
    try:
        yield path
    finally:
        app_db.SessionLocal.configure(bind=original_engine)
        app_db.engine.dispose()
        app_db.engine = original_engine
        from app import main as app_main
        app_main.engine = original_engine
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        config.settings.SQLITE_DB_PATH = original


@pytest.fixture()
def client(temp_db: str) -> Generator[TestClient, None, None]:
    app_db.Base.metadata.drop_all(bind=app_db.engine)
    app_db.Base.metadata.create_all(bind=app_db.engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client: TestClient) -> Callable[[str, str], Dict[str, str]]:
    def _fetch_pubkey() -> str:
        r = client.get("/auth/pubkey")
        assert r.status_code == 200, r.text
        pem = r.json().get("pem")
        assert pem, "Missing public key PEM"
        return pem

    def _encrypt(pem: str, plaintext: str) -> str:
        pub = serialization.load_pem_public_key(pem.encode("utf-8"))
        ct = pub.encrypt(
            plaintext.encode("utf-8"),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        return base64.b64encode(ct).decode("utf-8")

    def _create(email: str = "user@example.com", password: str = "1234", company: str = "TestCompany") -> Dict[str, str]:
        pem = _fetch_pubkey()
        enc_password = _encrypt(pem, password)
        register_resp = client.post("/auth/register", json={"email": email, "enc_password": enc_password, "company_name": company})
        if register_resp.status_code not in (200, 400):
            pytest.fail(f"Unexpected register status {register_resp.status_code}: {register_resp.text}")
        if register_resp.status_code == 400:
            detail = register_resp.json().get("detail")
            if detail != "Email already registered":
                pytest.fail(f"Unexpected register error: {detail}")
        login_resp = client.post("/auth/login", json={"email": email, "enc_password": enc_password})
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _create


@pytest.fixture()
def attach_vendor():
    def _attach(user_email: str, customer_id: int) -> None:
        db = app_db.SessionLocal()
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            user = db.query(User).filter(User.email == user_email).first()
            if not customer or not user:
                raise RuntimeError("Customer or user not found when attaching vendor")
            if user not in customer.vendors:
                customer.vendors.append(user)
                db.add(customer)
                db.commit()
        finally:
            db.close()

    return _attach
