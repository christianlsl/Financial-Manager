def test_update_customer_clear_company_clears_department(client, auth_headers):
    headers = auth_headers("owner@example.com")

    # Create Company
    company_resp = client.post(
        "/companies/",
        json={"name": "Test Company", "address": "Address"},
        headers=headers,
    )
    assert company_resp.status_code == 200
    company_id = company_resp.json()["id"]

    # Create Department
    department_resp = client.post(
        "/departments/",
        json={"name": "Test Dept", "company_id": company_id},
        headers=headers,
    )
    assert department_resp.status_code == 200
    department_id = department_resp.json()["id"]

    # Create Customer with Company and Department
    customer_resp = client.post(
        "/customers/",
        json={
            "name": "Test Customer",
            "company_id": company_id,
            "department_id": department_id,
            "email": "test@example.com",
        },
        headers=headers,
    )
    assert customer_resp.status_code == 200
    customer_id = customer_resp.json()["id"]
    customer_data = customer_resp.json()
    assert customer_data["company_id"] == company_id
    assert customer_data["department_id"] == department_id

    # Update Customer: Clear Company (set to 0)
    update_resp = client.put(
        f"/customers/{customer_id}",
        json={"company_id": 0},
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated_customer = update_resp.json()

    # Verify Company is 0 and Department is None
    assert updated_customer["company_id"] == 0
    assert updated_customer["department_id"] is None


def test_create_customer_with_company_0_clears_department(client, auth_headers):
    headers = auth_headers("owner@example.com")

    # Create Company
    company_resp = client.post(
        "/companies/",
        json={"name": "Test Company", "address": "Address"},
        headers=headers,
    )
    assert company_resp.status_code == 200
    company_id = company_resp.json()["id"]

    # Create Department
    department_resp = client.post(
        "/departments/",
        json={"name": "Test Dept", "company_id": company_id},
        headers=headers,
    )
    assert department_resp.status_code == 200
    department_id = department_resp.json()["id"]

    # Create Customer with Company 0 but Department set (should be cleared)
    customer_resp = client.post(
        "/customers/",
        json={
            "name": "Test Customer 2",
            "company_id": 0,
            "department_id": department_id,
            "email": "test2@example.com",
        },
        headers=headers,
    )
    assert customer_resp.status_code == 200
    customer_data = customer_resp.json()

    assert customer_data["company_id"] == 0
    assert customer_data["department_id"] is None
