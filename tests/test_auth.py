import time

from fastapi.testclient import TestClient

from app.auth.auth import COOKIE_NAME, hash_password
from main import create_app


def login_app(database_path):
    return create_app(
        database_path,
        api_token="",
        admin_username="研究员",
        admin_password_hash=hash_password("仅用于测试的密码123"),
    )


def test_login_required_by_default(database_path):
    with TestClient(
        create_app(database_path, api_token="", admin_username="", admin_password_hash="")
    ) as client:
        assert client.get("/", follow_redirects=False).headers["location"] == "/login"
        assert "登录研究工作台" in client.get("/login").text
        assert client.get("/api/v1/projects").status_code == 401
        response = client.post(
            "/api/v1/auth/login",
            headers={"X-GEO-Request": "1"},
            json={"username": "未知", "password": "未知"},
        )
        assert response.status_code == 503
        assert "尚未配置" in response.json()["detail"]


def test_login_and_logout(database_path):
    with TestClient(login_app(database_path), headers={"X-GEO-Request": "1"}) as client:
        wrong = client.post("/api/v1/auth/login", json={"username": "研究员", "password": "错误"})
        assert wrong.status_code == 401
        response = client.post(
            "/api/v1/auth/login", json={"username": "研究员", "password": "仅用于测试的密码123"}
        )
        assert response.status_code == 200
        assert (
            "HttpOnly" in response.headers["set-cookie"]
            and "SameSite=strict" in response.headers["set-cookie"]
        )
        assert client.get("/api/v1/auth/session").json()["username"] == "研究员"
        assert client.get("/").status_code == 200
        assert client.get("/login", follow_redirects=False).headers["location"] == "/"
        assert client.post("/api/v1/projects", json={"name": "登录验证", "brand": "星河"}).status_code == 201
        old_cookie = client.cookies.get(COOKIE_NAME)
        assert client.post("/api/v1/auth/logout").status_code == 200
        client.cookies.set(COOKIE_NAME, old_cookie)
        assert client.get("/api/v1/projects").status_code == 401


def test_mutation_requires_same_origin(client):
    assert client.post("/api/v1/auth/logout", headers={"Origin": "https://other.example"}).status_code == 403
    assert (
        client.post(
            "/api/v1/projects", headers={"X-GEO-Request": ""}, json={"name": "拦截", "brand": "星河"}
        ).status_code
        == 403
    )
    assert client.get("/api/v1/auth/session").status_code == 200


def test_rate_limit(database_path):
    with TestClient(login_app(database_path), headers={"X-GEO-Request": "1"}) as client:
        for _ in range(5):
            assert (
                client.post("/api/v1/auth/login", json={"username": "研究员", "password": "错误"}).status_code
                == 401
            )
        assert (
            client.post("/api/v1/auth/login", json={"username": "研究员", "password": "错误"}).status_code
            == 429
        )


def test_session_expiry_and_rotation(client):
    previous = client.cookies.get(COOKIE_NAME)
    assert (
        client.post(
            "/api/v1/auth/login", json={"username": "研究员", "password": "仅用于测试的密码123"}
        ).status_code
        == 200
    )
    assert not client.app.state.login.session(previous)
    current = client.cookies.get(COOKIE_NAME)
    client.app.state.login.sessions[current] = time.monotonic() - 1
    assert client.get("/api/v1/projects").status_code == 401
