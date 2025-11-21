def test_department_crud_flow(client, auth_headers, attach_vendor):
    headers = auth_headers("owner@example.com")
    company_resp = client.post(
        "/companies/",
        json={"name": "MainCorp"},
        headers=headers,
    )
    assert company_resp.status_code == 200, company_resp.text
    company_id = company_resp.json()["id"]

    create_resp = client.post(
        "/departments/",
        json={
            "name": "Sales",
            "company_id": company_id,
        },
        headers=headers,
    )
    assert create_resp.status_code == 200, create_resp.text
    department = create_resp.json()
    department_id = department["id"]
    assert department["company_id"] == company_id

    list_resp = client.get("/departments/", headers=headers)
    assert list_resp.status_code == 200
    assert any(item["id"] == department_id for item in list_resp.json())

    update_resp = client.put(
        f"/departments/{department_id}",
        json={"name": "Sales HQ"},
        headers=headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["name"] == "Sales HQ"
    assert update_resp.json()["company_id"] == company_id

    # Leader concept removed; previously invalid leader case no longer applicable.

    delete_resp = client.delete(f"/departments/{department_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True

    final_list = client.get("/departments/", headers=headers)
    assert final_list.status_code == 200
    assert all(item["id"] != department_id for item in final_list.json())
