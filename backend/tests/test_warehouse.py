def test_materials_stock(client, admin_headers):
    r = client.get("/api/stock/materials", headers=admin_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 8
    micro = next(i for i in items if i["material"]["sku"] == "MICROSPHERE")
    # 120 закупка - 100 списание - расход под ЗК-0001/0002 < min_stock 40
    assert micro["low_stock"] is True


def test_low_only_filter(client, admin_headers):
    all_items = client.get("/api/stock/materials", headers=admin_headers).json()
    low = client.get("/api/stock/materials?low_only=true", headers=admin_headers).json()
    assert 0 < len(low) < len(all_items)
    assert all(i["low_stock"] for i in low)


def test_purchase_move(client, store_headers):
    mats = client.get("/api/stock/materials", headers=store_headers).json()
    kov = next(i for i in mats if i["material"]["sku"] == "KOVELOS")
    before = kov["balance"]
    r = client.post(
        "/api/stock/moves",
        json={
            "material_id": kov["material"]["id"],
            "qty": 50,
            "type": "purchase",
            "note": "Дозакупка",
        },
        headers=store_headers,
    )
    assert r.status_code == 201, r.text
    after = client.get("/api/stock/materials", headers=store_headers).json()
    kov2 = next(i for i in after if i["material"]["sku"] == "KOVELOS")
    assert abs(kov2["balance"] - (before + 50)) < 1e-6


def test_writeoff_move_negative(client, store_headers):
    mats = client.get("/api/stock/materials", headers=store_headers).json()
    nit = next(i for i in mats if i["material"]["sku"] == "NITKA-ARM")
    r = client.post(
        "/api/stock/moves",
        json={
            "material_id": nit["material"]["id"],
            "qty": 10,
            "type": "writeoff",
            "note": "Порча",
        },
        headers=store_headers,
    )
    assert r.status_code == 201
    assert r.json()["qty"] == -10


def test_consumption_via_api_forbidden(client, store_headers):
    mats = client.get("/api/stock/materials", headers=store_headers).json()
    r = client.post(
        "/api/stock/moves",
        json={
            "material_id": mats[0]["material"]["id"],
            "qty": -5,
            "type": "consumption",
        },
        headers=store_headers,
    )
    assert r.status_code == 400


def test_operator_cannot_move(client, operator_headers):
    mats = client.get("/api/stock/materials", headers=operator_headers).json()
    r = client.post(
        "/api/stock/moves",
        json={"material_id": mats[0]["material"]["id"], "qty": 5, "type": "adjustment"},
        headers=operator_headers,
    )
    assert r.status_code == 403


def test_finished_goods(client, admin_headers):
    r = client.get("/api/stock/finished_goods", headers=admin_headers)
    assert r.status_code == 200
    pod = next(i for i in r.json() if i["product"]["sku"] == "POD-3232")
    assert pod["balance"] == 48  # 50 заказано, 2 брак, принято 48
