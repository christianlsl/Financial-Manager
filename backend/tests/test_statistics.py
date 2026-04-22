def test_statistics_supports_yearly_monthly_daily_granularity(client, auth_headers, attach_vendor):
    headers = auth_headers("stats@example.com")

    company_resp = client.post(
        "/companies/",
        json={"name": "Stats Co", "address": "Road 1"},
        headers=headers,
    )
    assert company_resp.status_code == 200, company_resp.text
    company_id = company_resp.json()["id"]

    customer_a_resp = client.post(
        "/customers/",
        json={"name": "Customer A", "company_id": company_id},
        headers=headers,
    )
    assert customer_a_resp.status_code == 200, customer_a_resp.text
    customer_a_id = customer_a_resp.json()["id"]
    attach_vendor("stats@example.com", customer_a_id)

    customer_b_resp = client.post(
        "/customers/",
        json={"name": "Customer B", "company_id": company_id},
        headers=headers,
    )
    assert customer_b_resp.status_code == 200, customer_b_resp.text
    customer_b_id = customer_b_resp.json()["id"]
    attach_vendor("stats@example.com", customer_b_id)

    type_resp = client.post("/types/", json={"name": "Stats Type"}, headers=headers)
    assert type_resp.status_code == 201, type_resp.text
    type_id = type_resp.json()["id"]

    def create_purchase(day: str, total: str):
        resp = client.post(
            "/purchases/",
            json={
                "date": day,
                "type_id": type_id,
                "items_count": 1,
                "unit_price": total,
                "total_price": total,
                "status": "done",
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    def create_sale(day: str, customer_id: int, total: str):
        resp = client.post(
            "/sales/",
            json={
                "date": day,
                "type_id": type_id,
                "customer_id": customer_id,
                "items_count": 1,
                "unit_price": total,
                "total_price": total,
                "status": "done",
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    create_purchase("2023-01-05", "100.00")
    create_purchase("2024-03-10", "200.00")
    create_purchase("2024-03-11", "150.00")
    create_purchase("2025-02-01", "300.00")

    create_sale("2023-01-05", customer_a_id, "180.00")
    create_sale("2024-03-10", customer_a_id, "320.00")
    create_sale("2024-03-11", customer_b_id, "260.00")
    create_sale("2025-02-01", customer_a_id, "500.00")

    common_params = {
        "start_date": "2023-01-01",
        "end_date": "2025-12-31",
    }

    yearly_resp = client.get(
        "/statistics/",
        params={**common_params, "analysis_type": "yearly"},
        headers=headers,
    )
    assert yearly_resp.status_code == 200, yearly_resp.text
    yearly = yearly_resp.json()
    assert yearly["trend"]["analysisType"] == "yearly"
    assert yearly["trend"]["categories"] == ["2023", "2024", "2025"]
    assert yearly["customerAnalysis"]["categories"] == ["2023", "2024", "2025"]

    monthly_resp = client.get(
        "/statistics/",
        params={**common_params, "analysis_type": "monthly"},
        headers=headers,
    )
    assert monthly_resp.status_code == 200, monthly_resp.text
    monthly = monthly_resp.json()
    assert monthly["trend"]["analysisType"] == "monthly"
    assert monthly["trend"]["categories"] == ["2023-01", "2024-03", "2025-02"]
    assert monthly["customerAnalysis"]["categories"] == ["2023-01", "2024-03", "2025-02"]

    daily_resp = client.get(
        "/statistics/",
        params={**common_params, "analysis_type": "daily"},
        headers=headers,
    )
    assert daily_resp.status_code == 200, daily_resp.text
    daily = daily_resp.json()
    assert daily["trend"]["analysisType"] == "daily"
    assert daily["trend"]["categories"] == ["2023-01-05", "2024-03-10", "2024-03-11", "2025-02-01"]
    assert daily["customerAnalysis"]["categories"] == ["2023-01-05", "2024-03-10", "2024-03-11", "2025-02-01"]


def test_statistics_invalid_analysis_type_returns_400(client, auth_headers):
    headers = auth_headers("stats-invalid@example.com")

    resp = client.get("/statistics/", params={"analysis_type": "weekly"}, headers=headers)
    assert resp.status_code == 400
    assert "analysis_type" in resp.json()["detail"]


def test_statistics_profit_rate_is_zero_when_sale_total_zero(client, auth_headers):
    headers = auth_headers("stats-profit@example.com")

    type_resp = client.post("/types/", json={"name": "Zero Sale Type"}, headers=headers)
    assert type_resp.status_code == 201, type_resp.text
    type_id = type_resp.json()["id"]

    purchase_resp = client.post(
        "/purchases/",
        json={
            "date": "2024-01-10",
            "type_id": type_id,
            "items_count": 1,
            "unit_price": "99.00",
            "total_price": "99.00",
            "status": "done",
        },
        headers=headers,
    )
    assert purchase_resp.status_code == 200, purchase_resp.text

    stats_resp = client.get(
        "/statistics/",
        params={
            "analysis_type": "monthly",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
        headers=headers,
    )
    assert stats_resp.status_code == 200, stats_resp.text
    body = stats_resp.json()
    assert body["overview"]["saleTotal"] == 0.0
    assert body["overview"]["profitRate"] == 0.0
