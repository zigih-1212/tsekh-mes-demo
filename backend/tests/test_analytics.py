def test_overview(client, admin_headers):
    r = client.get("/api/analytics/overview", headers=admin_headers)
    assert r.status_code == 200
    o = r.json()
    assert o["orders_total"] >= 3
    assert o["orders_by_status"].get("completed", 0) >= 1
    assert o["produced_qty"] >= 48
    assert o["defect_qty"] >= 2
    assert 0 <= o["defect_rate"] <= 100
    assert o["payroll_total"] > 0
    assert any(op["name"] for op in o["payroll_by_operator"])
    assert any(m["material"]["sku"] == "MICROSPHERE" for m in o["low_stock_materials"])
    assert any(p["qty"] >= 48 for p in o["production_by_product"])


def test_overview_requires_auth(client):
    assert client.get("/api/analytics/overview").status_code == 401
