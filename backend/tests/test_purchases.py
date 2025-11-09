def test_purchase_crud_flow_with_owned_relations(client, auth_headers):
    headers = auth_headers("owner@example.com")
    company_resp = client.post(
        "/companies/",
        json={"name": "BuyerCo", "address": "Market Street"},
        headers=headers,
    )
    assert company_resp.status_code == 200, company_resp.text
    company_id = company_resp.json()["id"]

    type_resp = client.post("/types/", json={"name": "Office Supplies"}, headers=headers)
    assert type_resp.status_code == 201, type_resp.text
    type_id = type_resp.json()["id"]

    payload = {
        "date": "2024-01-01",
        "company_id": company_id,
        "type_id": type_id,
        "item_name": "Printer Paper",
        "items_count": 10,
        "total_price": "199.90",
        "status": "ordered",
        "notes": "First batch",
    }
    create_resp = client.post("/purchases/", json=payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    purchase = create_resp.json()
    purchase_id = purchase["id"]
    assert purchase["company_id"] == company_id
    assert purchase["type_id"] == type_id

    list_resp = client.get("/purchases/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    detail_resp = client.get(f"/purchases/{purchase_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "ordered"

    update_resp = client.put(
        f"/purchases/{purchase_id}",
        json={"status": "received", "items_count": 12},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "received"
    assert update_resp.json()["items_count"] == 12

    delete_resp = client.delete(f"/purchases/{purchase_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True

    assert client.get("/purchases/", headers=headers).json() == []


def test_purchase_validations_for_foreign_references(client, auth_headers):
    owner_headers = auth_headers("owner@example.com")
    company_create = client.post(
        "/companies/",
        json={"name": "OwnerBuyer", "address": "North Road"},
        headers=owner_headers,
    )
    assert company_create.status_code == 200, company_create.text
    company_id = company_create.json()["id"]
    type_create = client.post("/types/", json={"name": "OwnerType"}, headers=owner_headers)
    assert type_create.status_code == 201, type_create.text
    type_id = type_create.json()["id"]

    other_headers = auth_headers("other@example.com")

    payload_type = {
        "date": "2024-02-01",
        "type_id": type_id,
        "items_count": 5,
        "total_price": "75.00",
        "status": "pending",
    }
    type_resp = client.post("/purchases/", json=payload_type, headers=other_headers)
    assert type_resp.status_code == 404
    assert type_resp.json()["detail"] == "Type not found"

    payload_company = {
        "date": "2024-02-02",
        "company_id": company_id,
        "items_count": 7,
        "total_price": "150.00",
        "status": "pending",
    }
    company_resp = client.post("/purchases/", json=payload_company, headers=other_headers)
    assert company_resp.status_code == 404
    assert company_resp.json()["detail"] == "Company not found"

    create_resp = client.post(
        "/purchases/",
        json={
            "date": "2024-02-10",
            "company_id": company_id,
            "type_id": type_id,
            "items_count": 3,
            "total_price": "60.00",
            "status": "ordered",
        },
        headers=owner_headers,
    )
    assert create_resp.status_code == 200
    purchase_id = create_resp.json()["id"]

    foreign_type_resp = client.post(
        "/types/",
        json={"name": "ForeignType"},
        headers=other_headers,
    )
    assert foreign_type_resp.status_code == 201, foreign_type_resp.text
    foreign_type_id = foreign_type_resp.json()["id"]
    update_type_resp = client.put(
        f"/purchases/{purchase_id}",
        json={"type_id": foreign_type_id},
        headers=owner_headers,
    )
    assert update_type_resp.status_code == 404
    assert update_type_resp.json()["detail"] == "Type not found"

    foreign_company_resp = client.post(
        "/companies/",
        json={"name": "ForeignCo", "address": "Elsewhere"},
        headers=other_headers,
    )
    assert foreign_company_resp.status_code == 200, foreign_company_resp.text
    foreign_company_id = foreign_company_resp.json()["id"]
    update_company_resp = client.put(
        f"/purchases/{purchase_id}",
        json={"company_id": foreign_company_id},
        headers=owner_headers,
    )
    assert update_company_resp.status_code == 404
    assert update_company_resp.json()["detail"] == "Company not found"
