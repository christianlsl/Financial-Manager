def test_sale_crud_flow_with_owned_relations(client, auth_headers, attach_vendor):
    headers = auth_headers("owner@example.com")
    company_resp = client.post(
        "/companies/",
        json={"name": "SellerCo", "address": "Warehouse"},
        headers=headers,
    )
    assert company_resp.status_code == 200, company_resp.text
    company_id = company_resp.json()["id"]

    customer_resp = client.post(
        "/customers/",
        json={"name": "Client A", "company_id": company_id, "email": "client@example.com"},
        headers=headers,
    )
    assert customer_resp.status_code == 200, customer_resp.text
    customer_id = customer_resp.json()["id"]
    attach_vendor("owner@example.com", customer_id)

    type_resp = client.post("/types/", json={"name": "Electronics"}, headers=headers)
    assert type_resp.status_code == 201, type_resp.text
    type_id = type_resp.json()["id"]

    payload = {
        "date": "2024-03-01",
        "type_id": type_id,
        "customer_id": customer_id,
        "item_name": "Monitors",
        "items_count": 4,
        "unit_price": "224.75",
        "total_price": "899.00",
        "status": "sent",
        "notes": "Priority",
    }
    create_resp = client.post("/sales/", json=payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    sale = create_resp.json()
    sale_id = sale["id"]
    assert sale["type_id"] == type_id
    assert sale["customer_id"] == customer_id
    assert "company_id" not in sale
    assert sale["image_url"] is None

    list_resp = client.get("/sales/", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 1
    assert len(list_data["items"]) == 1

    detail_resp = client.get(f"/sales/{sale_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "sent"

    image_url = "https://cdn.example.com/sales/img-1.jpg"
    update_resp = client.put(
        f"/sales/{sale_id}",
        json={"status": "paid", "items_count": 5, "image_url": image_url},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "paid"
    assert update_resp.json()["items_count"] == 5
    assert update_resp.json()["total_price"] == "1123.75"
    assert update_resp.json()["image_url"] == image_url

    delete_resp = client.delete(f"/sales/{sale_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True

    final_list = client.get("/sales/", headers=headers)
    assert final_list.status_code == 200
    assert final_list.json() == {"items": [], "total": 0}


def test_sale_validations_for_foreign_references(client, auth_headers, attach_vendor):
    owner_headers = auth_headers("owner@example.com")
    type_create = client.post("/types/", json={"name": "OwnerSaleType"}, headers=owner_headers)
    assert type_create.status_code == 201, type_create.text
    type_id = type_create.json()["id"]

    company_create = client.post(
        "/companies/",
        json={"name": "OwnerSeller", "address": "South Ave"},
        headers=owner_headers,
    )
    assert company_create.status_code == 200, company_create.text
    company_id = company_create.json()["id"]

    owner_customer_resp = client.post(
        "/customers/",
        json={"name": "Primary Buyer", "company_id": company_id},
        headers=owner_headers,
    )
    assert owner_customer_resp.status_code == 200, owner_customer_resp.text
    owner_customer_id = owner_customer_resp.json()["id"]
    attach_vendor("owner@example.com", owner_customer_id)

    other_headers = auth_headers("other@example.com")
    other_customer_resp = client.post(
        "/customers/",
        json={"name": "Other Personal", "company_id": 0},
        headers=other_headers,
    )
    assert other_customer_resp.status_code == 200, other_customer_resp.text
    other_customer_id = other_customer_resp.json()["id"]
    assert other_customer_resp.json()["company_id"] == 0

    payload_type = {
        "date": "2024-04-01",
        "type_id": type_id,
        "items_count": 2,
        "unit_price": "150.00",
        "total_price": "300.00",
        "status": "draft",
        "customer_id": other_customer_id,
    }
    type_resp = client.post("/sales/", json=payload_type, headers=other_headers)
    assert type_resp.status_code == 404
    assert type_resp.json()["detail"] == "Type not found"

    create_resp = client.post(
        "/sales/",
        json={
            "date": "2024-04-10",
            "type_id": type_id,
            "items_count": 3,
            "unit_price": "170.00",
            "total_price": "510.00",
            "status": "sent",
            "customer_id": owner_customer_id,
        },
        headers=owner_headers,
    )
    assert create_resp.status_code == 200
    sale_id = create_resp.json()["id"]

    # Owner cannot create sales for customers they do not have access to
    forbidden_customer_resp = client.post(
        "/sales/",
        json={
            "date": "2024-04-12",
            "customer_id": other_customer_id,
            "items_count": 1,
            "unit_price": "100.00",
            "total_price": "100.00",
            "status": "draft",
        },
        headers=owner_headers,
    )
    assert forbidden_customer_resp.status_code == 404
    assert forbidden_customer_resp.json()["detail"] == "Customer not found"

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

    attach_customer_resp = client.put(
        f"/sales/{sale_id}",
        json={"customer_id": other_customer_id},
        headers=owner_headers,
    )
    assert attach_customer_resp.status_code == 404
    assert attach_customer_resp.json()["detail"] == "Customer not found"

    second_customer_resp = client.post(
        "/customers/",
        json={"name": "Buyer", "company_id": company_id},
        headers=owner_headers,
    )
    assert second_customer_resp.status_code == 200, second_customer_resp.text
    second_customer_id = second_customer_resp.json()["id"]
    attach_vendor("owner@example.com", second_customer_id)

    reassign_customer_resp = client.put(
        f"/sales/{sale_id}",
        json={"customer_id": second_customer_id},
        headers=owner_headers,
    )
    assert reassign_customer_resp.status_code == 200
    assert reassign_customer_resp.json()["customer_id"] == second_customer_id


def test_sales_filters_support(client, auth_headers, attach_vendor):
    headers = auth_headers("owner@example.com")
    company_a = client.post("/companies/", json={"name": "Alpha Holdings"}, headers=headers)
    assert company_a.status_code == 200, company_a.text
    company_a_id = company_a.json()["id"]

    company_b = client.post("/companies/", json={"name": "Beta Works"}, headers=headers)
    assert company_b.status_code == 200, company_b.text
    company_b_id = company_b.json()["id"]

    customer_a = client.post(
        "/customers/",
        json={"name": "Alpha Client", "company_id": company_a_id},
        headers=headers,
    )
    assert customer_a.status_code == 200, customer_a.text
    customer_a_id = customer_a.json()["id"]
    attach_vendor("owner@example.com", customer_a_id)

    customer_b = client.post(
        "/customers/",
        json={"name": "Beta Client", "company_id": company_b_id},
        headers=headers,
    )
    assert customer_b.status_code == 200, customer_b.text
    customer_b_id = customer_b.json()["id"]
    attach_vendor("owner@example.com", customer_b_id)

    type_resp = client.post("/types/", json={"name": "FilterType"}, headers=headers)
    assert type_resp.status_code == 201, type_resp.text
    type_id = type_resp.json()["id"]

    def create_sale(date, customer_id, item_name, status, unit_price="100.00"):
        resp = client.post(
            "/sales/",
            json={
                "date": date,
                "type_id": type_id,
                "customer_id": customer_id,
                "item_name": item_name,
                "items_count": 1,
                "unit_price": unit_price,
                "total_price": unit_price,
                "status": status,
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["id"]

    sale_alpha_draft = create_sale("2024-05-01", customer_a_id, "Expo Booth", "draft")
    sale_beta_sent = create_sale("2024-05-12", customer_b_id, "Conference Banner", "sent")
    sale_alpha_paid = create_sale("2024-06-02", customer_a_id, "Roadshow Stand", "paid")
    sale_beta_high = create_sale("2024-06-15", customer_b_id, "Mega Stand", "paid", unit_price="850.00")

    def fetch_ids(params):
        resp = client.get("/sales/", params=params, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        return {item["id"] for item in data["items"]}, data["total"]

    ids, total = fetch_ids({"search": "expo"})
    assert ids == {sale_alpha_draft}
    assert total == 1

    ids, total = fetch_ids({"search": "beta"})
    assert ids == {sale_beta_sent, sale_beta_high}
    assert total == 2

    ids, total = fetch_ids({"search": "holdings"})
    assert ids == {sale_alpha_draft, sale_alpha_paid}
    assert total == 2

    ids, total = fetch_ids({"company_id": company_a_id})
    assert ids == {sale_alpha_draft, sale_alpha_paid}
    assert total == 2

    ids, total = fetch_ids({"status": "paid"})
    assert ids == {sale_alpha_paid, sale_beta_high}
    assert total == 2

    ids, total = fetch_ids({"date_from": "2024-05-10", "date_to": "2024-05-20"})
    assert ids == {sale_beta_sent}
    assert total == 1

    ids, total = fetch_ids({"amount_min": 500})
    assert ids == {sale_beta_high}
    assert total == 1

    ids, total = fetch_ids({"amount_max": 150})
    assert ids == {sale_alpha_draft, sale_alpha_paid, sale_beta_sent}
    assert total == 3
