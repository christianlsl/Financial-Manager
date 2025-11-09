def test_type_crud_flow(client, auth_headers):
    headers = auth_headers()

    create_resp = client.post("/types/", json={"name": "Hardware"}, headers=headers)
    assert create_resp.status_code == 201, create_resp.text
    type_obj = create_resp.json()
    type_id = type_obj["id"]
    assert type_obj["name"] == "Hardware"

    list_resp = client.get("/types/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    detail_resp = client.get(f"/types/{type_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["owner_id"] == type_obj["owner_id"]

    update_resp = client.put(f"/types/{type_id}", json={"name": "Hardware Pro"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Hardware Pro"

    delete_resp = client.delete(f"/types/{type_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True

    missing_resp = client.get(f"/types/{type_id}", headers=headers)
    assert missing_resp.status_code == 404
    assert client.get("/types/", headers=headers).json() == []


def test_type_isolation(client, auth_headers):
    owner_headers = auth_headers("owner@example.com")
    create_resp = client.post("/types/", json={"name": "Confidential"}, headers=owner_headers)
    assert create_resp.status_code == 201
    type_id = create_resp.json()["id"]

    other_headers = auth_headers("other@example.com")
    detail_resp = client.get(f"/types/{type_id}", headers=other_headers)
    assert detail_resp.status_code == 404

    update_resp = client.put(
        f"/types/{type_id}",
        json={"name": "Leak"},
        headers=other_headers,
    )
    assert update_resp.status_code == 404

    delete_resp = client.delete(f"/types/{type_id}", headers=other_headers)
    assert delete_resp.status_code == 404

    list_resp = client.get("/types/", headers=other_headers)
    assert list_resp.status_code == 200
    assert list_resp.json() == []
