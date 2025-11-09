def test_sale_crud_flow_with_owned_relations(client, auth_headers):
    headers = auth_headers("owner@example.com")
    company_resp = client.post(
        "/companies/",
        json={"name": "SellerCo", "address": "Warehouse"},
        headers=headers,
    )
    assert company_resp.status_code == 200, company_resp.text
    company_id = company_resp.json()["id"]

    type_resp = client.post("/types/", json={"name": "Electronics"}, headers=headers)
    assert type_resp.status_code == 201, type_resp.text
    type_id = type_resp.json()["id"]

    payload = {
        "date": "2024-03-01",
        "company_id": company_id,
        "type_id": type_id,
        "item_name": "Monitors",
        "items_count": 4,
        "total_price": "899.00",
        "status": "sent",
        "notes": "Priority",
    }
    create_resp = client.post("/sales/", json=payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    sale = create_resp.json()
    sale_id = sale["id"]
    assert sale["company_id"] == company_id
    assert sale["type_id"] == type_id

    list_resp = client.get("/sales/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    detail_resp = client.get(f"/sales/{sale_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "sent"

    update_resp = client.put(
        f"/sales/{sale_id}",
        json={"status": "paid", "items_count": 5},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "paid"
    assert update_resp.json()["items_count"] == 5

    delete_resp = client.delete(f"/sales/{sale_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True

    assert client.get("/sales/", headers=headers).json() == []


def test_sale_validations_for_foreign_references(client, auth_headers):
    owner_headers = auth_headers("owner@example.com")
    company_create = client.post(
        "/companies/",
        json={"name": "OwnerSeller", "address": "South Ave"},
        headers=owner_headers,
    )
    assert company_create.status_code == 200, company_create.text
    company_id = company_create.json()["id"]
    type_create = client.post("/types/", json={"name": "OwnerSaleType"}, headers=owner_headers)
    assert type_create.status_code == 201, type_create.text
    type_id = type_create.json()["id"]

    other_headers = auth_headers("other@example.com")

    payload_type = {
        "date": "2024-04-01",
        "type_id": type_id,
        "items_count": 2,
        "total_price": "300.00",
        "status": "draft",
    }
    type_resp = client.post("/sales/", json=payload_type, headers=other_headers)
    assert type_resp.status_code == 404
    assert type_resp.json()["detail"] == "Type not found"

    payload_company = {
        "date": "2024-04-02",
        "company_id": company_id,
        "items_count": 6,
        "total_price": "450.00",
        "status": "draft",
    }
    company_resp = client.post("/sales/", json=payload_company, headers=other_headers)
    assert company_resp.status_code == 404
    assert company_resp.json()["detail"] == "Company not found"

    create_resp = client.post(
        "/sales/",
        json={
            "date": "2024-04-10",
            "company_id": company_id,
            "type_id": type_id,
            "items_count": 3,
            "total_price": "510.00",
            "status": "sent",
        },
        headers=owner_headers,
    )
    assert create_resp.status_code == 200
    sale_id = create_resp.json()["id"]

    foreign_type_resp = client.post(
        "/types/",
        json={"name": "SaleForeignType"},
        headers=other_headers,
    )
    assert foreign_type_resp.status_code == 201, foreign_type_resp.text
    foreign_type_id = foreign_type_resp.json()["id"]
    update_type_resp = client.put(
        f"/sales/{sale_id}",
        json={"type_id": foreign_type_id},
        headers=owner_headers,
    )
    assert update_type_resp.status_code == 404
    assert update_type_resp.json()["detail"] == "Type not found"

    foreign_company_resp = client.post(
        "/companies/",
        json={"name": "SaleForeignCo", "address": "Remote"},
        headers=other_headers,
    )
    assert foreign_company_resp.status_code == 200, foreign_company_resp.text
    foreign_company_id = foreign_company_resp.json()["id"]
    update_company_resp = client.put(
        f"/sales/{sale_id}",
        json={"company_id": foreign_company_id},
        headers=owner_headers,
    )
    assert update_company_resp.status_code == 404
    assert update_company_resp.json()["detail"] == "Company not found"
