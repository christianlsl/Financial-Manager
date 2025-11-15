def test_purchase_crud_flow_with_owned_relations(client, auth_headers, attach_vendor):
    headers = auth_headers("owner@example.com")
    company_resp = client.post(
        "/companies/",
        json={"name": "BuyerCo", "address": "Market Street"},
        headers=headers,
    )
    assert company_resp.status_code == 200, company_resp.text
    company_id = company_resp.json()["id"]

    customer_resp = client.post(
        "/customers/",
        json={"name": "Alice", "company_id": company_id, "email": "alice@example.com"},
        headers=headers,
    )
    assert customer_resp.status_code == 200, customer_resp.text
    customer_id = customer_resp.json()["id"]
    attach_vendor("owner@example.com", customer_id)

    type_resp = client.post("/types/", json={"name": "Office Supplies"}, headers=headers)
    assert type_resp.status_code == 201, type_resp.text
    type_id = type_resp.json()["id"]

    payload = {
        "date": "2024-01-01",
        "type_id": type_id,
        "customer_id": customer_id,
        "item_name": "Printer Paper",
        "items_count": 10,
        "unit_price": "19.99",
        "total_price": "199.90",
        "status": "ordered",
        "notes": "First batch",
    }
    create_resp = client.post("/purchases/", json=payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    purchase = create_resp.json()
    purchase_id = purchase["id"]
    assert purchase["type_id"] == type_id
    assert purchase["customer_id"] == customer_id
    assert "company_id" not in purchase

    list_resp = client.get("/purchases/", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 1
    assert len(list_data["items"]) == 1

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
    assert update_resp.json()["total_price"] == "239.88"

    delete_resp = client.delete(f"/purchases/{purchase_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True

    final_list = client.get("/purchases/", headers=headers)
    assert final_list.status_code == 200
    assert final_list.json() == {"items": [], "total": 0}


def test_purchase_validations_for_foreign_references(client, auth_headers, attach_vendor):
    owner_headers = auth_headers("owner@example.com")
    type_create = client.post("/types/", json={"name": "OwnerType"}, headers=owner_headers)
    assert type_create.status_code == 201, type_create.text
    type_id = type_create.json()["id"]

    company_create = client.post(
        "/companies/",
        json={"name": "OwnerBuyer", "address": "North Road"},
        headers=owner_headers,
    )
    assert company_create.status_code == 200, company_create.text
    company_id = company_create.json()["id"]

    owner_customer_resp = client.post(
        "/customers/",
        json={"name": "Primary Supplier", "company_id": company_id},
        headers=owner_headers,
    )
    assert owner_customer_resp.status_code == 200, owner_customer_resp.text
    owner_customer_id = owner_customer_resp.json()["id"]
    attach_vendor("owner@example.com", owner_customer_id)

    other_headers = auth_headers("other@example.com")
    other_customer_resp = client.post(
        "/customers/",
        json={"name": "Other Supplier", "company_id": 0},
        headers=other_headers,
    )
    assert other_customer_resp.status_code == 200, other_customer_resp.text
    other_customer_id = other_customer_resp.json()["id"]
    assert other_customer_resp.json()["company_id"] == 0

    payload_type = {
        "date": "2024-02-01",
        "type_id": type_id,
        "items_count": 5,
        "unit_price": "15.00",
        "total_price": "75.00",
        "status": "pending",
        "customer_id": other_customer_id,
    }
    type_resp = client.post("/purchases/", json=payload_type, headers=other_headers)
    assert type_resp.status_code == 404
    assert type_resp.json()["detail"] == "Type not found"

    create_resp = client.post(
        "/purchases/",
        json={
            "date": "2024-02-10",
            "type_id": type_id,
            "items_count": 3,
            "unit_price": "20.00",
            "total_price": "60.00",
            "status": "ordered",
            "customer_id": owner_customer_id,
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

    # Attempt to mismatch company when a customer already linked
    attach_customer_resp = client.put(
        f"/purchases/{purchase_id}",
        json={"customer_id": other_customer_id},
        headers=owner_headers,
    )
    assert attach_customer_resp.status_code == 404
    assert attach_customer_resp.json()["detail"] == "Customer not found"

    customer_resp = client.post(
        "/customers/",
        json={"name": "Bob", "company_id": company_id},
        headers=owner_headers,
    )
    assert customer_resp.status_code == 200, customer_resp.text
    customer_id = customer_resp.json()["id"]
    attach_vendor("owner@example.com", customer_id)

    reassign_customer_resp = client.put(
        f"/purchases/{purchase_id}",
        json={"customer_id": customer_id},
        headers=owner_headers,
    )
    assert reassign_customer_resp.status_code == 200
    assert reassign_customer_resp.json()["customer_id"] == customer_id
