def test_register_and_login(client):
    register_resp = client.post("/auth/register", json={"email": "user@example.com", "password": "1234"})
    if register_resp.status_code != 200:
        assert register_resp.status_code == 400, register_resp.text
        assert register_resp.json()["detail"] == "Email already registered"
    else:
        assert register_resp.status_code == 200, register_resp.text
        assert register_resp.json()["email"] == "user@example.com"

    login_resp = client.post("/auth/login", json={"email": "user@example.com", "password": "1234"})
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    assert token
