def test_list_orders_seeded(client, admin_headers):
    r = client.get("/api/orders", headers=admin_headers)
    assert r.status_code == 200
    numbers = {o["number"] for o in r.json()}
    assert {"ЗК-0001", "ЗК-0002", "ЗК-0003"} <= numbers


def test_create_and_release_order(client, admin_headers):
    # новый заказ на повязку
    products = client.get("/api/products", headers=admin_headers).json()
    pov = next(p for p in products if p["sku"] == "POV-NOGA-S1")
    r = client.post(
        "/api/orders",
        json={"product_id": pov["id"], "qty": 10},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["status"] == "planned"

    # выпускаем
    r = client.post(f"/api/orders/{order['id']}/release", headers=admin_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "released"
    detail = client.get(f"/api/products/{pov['id']}", headers=admin_headers).json()
    assert len(body["tasks"]) == len(detail["routing"])
    # задания созданы со ставками
    assert all(t["rate"] > 0 for t in body["tasks"])
    # расход материалов создан
    moves = client.get("/api/stock/moves", headers=admin_headers).json()
    cons = [
        m for m in moves if m["order_id"] == order["id"] and m["type"] == "consumption"
    ]
    assert cons and all(m["qty"] < 0 for m in cons)

    # повторный выпуск невозможен
    r = client.post(f"/api/orders/{order['id']}/release", headers=admin_headers)
    assert r.status_code == 409


def test_release_insufficient_stock(client, admin_headers):
    products = client.get("/api/products", headers=admin_headers).json()
    pod = next(p for p in products if p["sku"] == "POD-3232")
    r = client.post(
        "/api/orders",
        json={"product_id": pod["id"], "qty": 100000},
        headers=admin_headers,
    )
    order_id = r.json()["id"]
    r = client.post(f"/api/orders/{order_id}/release", headers=admin_headers)
    assert r.status_code == 409
    assert "Не хватает материалов" in r.json()["detail"]
    # отменяем, т.к. заказ остался planned
    r = client.post(f"/api/orders/{order_id}/cancel", headers=admin_headers)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"


def test_task_lifecycle(
    client, admin_headers, foreman_headers, operator_headers, operator2_headers
):
    # берём заказ ЗК-0002 (in_progress), назначаем новое задание op1 и закрываем
    orders = client.get("/api/orders", headers=admin_headers).json()
    o2 = next(o for o in orders if o["number"] == "ЗК-0002")
    tasks = client.get(f"/api/orders/{o2['id']}/tasks", headers=admin_headers).json()
    pending = next(t for t in tasks if t["status"] == "pending")
    op1 = client.get("/api/users", headers=admin_headers).json()
    op1 = next(u for u in op1 if u["email"] == "op1@artraid.demo")

    r = client.post(
        f"/api/tasks/{pending['id']}/assign",
        json={"user_id": op1["id"]},
        headers=foreman_headers,
    )
    assert r.status_code == 200 and r.json()["assignee_id"] == op1["id"]

    # чужой оператор не может стартовать
    r = client.post(f"/api/tasks/{pending['id']}/start", headers=operator2_headers)
    assert r.status_code == 403

    # назначенный стартует
    r = client.post(f"/api/tasks/{pending['id']}/start", headers=operator_headers)
    assert r.status_code == 200 and r.json()["status"] == "in_progress"

    # completed: done+rejected > qty -> 409
    r = client.post(
        f"/api/tasks/{pending['id']}/complete",
        json={"qty_done": pending["qty"] + 1, "qty_rejected": 0},
        headers=operator_headers,
    )
    assert r.status_code == 409

    r = client.post(
        f"/api/tasks/{pending['id']}/complete",
        json={"qty_done": pending["qty"], "qty_rejected": 0},
        headers=operator_headers,
    )
    assert r.status_code == 200 and r.json()["status"] == "done"


def test_receive_fg_completes_order(client, admin_headers, store_headers):
    orders = client.get("/api/orders", headers=admin_headers).json()
    o2 = next(o for o in orders if o["number"] == "ЗК-0002")
    detail = client.get(f"/api/orders/{o2['id']}", headers=admin_headers).json()
    remaining = o2["qty"] - detail["received_qty"]
    assert remaining > 0
    r = client.post(
        f"/api/orders/{o2['id']}/receive_fg",
        json={"qty": remaining, "note": "Финальная приёмка"},
        headers=store_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"
    assert r.json()["received_qty"] == o2["qty"]

    # сверх задания — нельзя
    r = client.post(
        f"/api/orders/{o2['id']}/receive_fg", json={"qty": 1}, headers=store_headers
    )
    assert r.status_code == 409


def test_operator_cannot_create_order(client, operator_headers):
    products = client.get("/api/products", headers=operator_headers).json()
    r = client.post(
        "/api/orders",
        json={"product_id": products[0]["id"], "qty": 1},
        headers=operator_headers,
    )
    assert r.status_code == 403
