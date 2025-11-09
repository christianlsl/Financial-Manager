def test_company_crud_flow(client, auth_headers):
    headers = auth_headers()
    payload = {
        "name": "Acme Corp",
        "address": "123 Main St",
        "legal_person": "Alice",
        "phone": "1234567890",
    "email": "contact@acme.com",
    }
    create_resp = client.post("/companies/", json=payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    company = create_resp.json()
    company_id = company["id"]
    assert company["name"] == payload["name"]

    list_resp = client.get("/companies/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    detail_resp = client.get(f"/companies/{company_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["name"] == payload["name"]

    update_resp = client.put(f"/companies/{company_id}", json={"phone": "5550000"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["phone"] == "5550000"

    delete_resp = client.delete(f"/companies/{company_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True

    missing_resp = client.get(f"/companies/{company_id}", headers=headers)
    assert missing_resp.status_code == 404
    assert client.get("/companies/", headers=headers).json() == []


def test_company_isolation(client, auth_headers):
    owner_headers = auth_headers("owner@example.com")
    create_resp = client.post(
        "/companies/",
        json={"name": "OwnerCo", "address": "A St"},
        headers=owner_headers,
    )
    assert create_resp.status_code == 200, create_resp.text
    company_id = create_resp.json()["id"]

    other_headers = auth_headers("other@example.com")
    detail_resp = client.get(f"/companies/{company_id}", headers=other_headers)
    assert detail_resp.status_code == 404

    update_resp = client.put(
        f"/companies/{company_id}",
        json={"phone": "000"},
        headers=other_headers,
    )
    assert update_resp.status_code == 404

    delete_resp = client.delete(f"/companies/{company_id}", headers=other_headers)
    assert delete_resp.status_code == 404

    list_resp = client.get("/companies/", headers=other_headers)
    assert list_resp.status_code == 200
    assert list_resp.json() == []
