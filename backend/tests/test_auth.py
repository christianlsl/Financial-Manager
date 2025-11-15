import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


def _encrypt_with_pem(pem: str, plaintext: str) -> str:
    pub = serialization.load_pem_public_key(pem.encode("utf-8"))
    ct = pub.encrypt(
        plaintext.encode("utf-8"),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return base64.b64encode(ct).decode("utf-8")


def test_register_and_login(client):
    pubkey_resp = client.get("/auth/pubkey")
    assert pubkey_resp.status_code == 200, pubkey_resp.text
    pem = pubkey_resp.json()["pem"]
    enc_password = _encrypt_with_pem(pem, "1234")

    register_resp = client.post("/auth/register", json={"email": "user@example.com", "enc_password": enc_password, "company_name": "TestCompany"})
    if register_resp.status_code != 200:
        assert register_resp.status_code == 400, register_resp.text
        assert register_resp.json()["detail"] == "Email already registered"
    else:
        assert register_resp.status_code == 200, register_resp.text
        assert register_resp.json()["email"] == "user@example.com"
        assert register_resp.json()["company_name"] == "TestCompany"

    login_resp = client.post("/auth/login", json={"email": "user@example.com", "enc_password": enc_password})
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    assert token
