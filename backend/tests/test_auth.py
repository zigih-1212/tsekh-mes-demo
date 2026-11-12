def test_login_ok(client):
    r = client.post(
        "/api/auth/login",
        data={"username": "admin@artraid.demo", "password": "admin123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "admin"


def test_login_wrong_password(client):
    r = client.post(
        "/api/auth/login",
        data={"username": "admin@artraid.demo", "password": "wrong"},
    )
    assert r.status_code == 401


def test_me(client, admin_headers):
    r = client.get("/api/auth/me", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "admin@artraid.demo"


def test_me_no_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_users_admin_only(client, operator_headers):
    assert client.get("/api/users", headers=operator_headers).status_code == 403


def test_users_list_admin(client, admin_headers):
    r = client.get("/api/users", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 7
