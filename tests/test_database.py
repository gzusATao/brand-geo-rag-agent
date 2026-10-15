from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.libs.database import Database, MySQLResult, format_row, mysql_parameters
from main import create_app
from scripts.create_admin import create_admin


def test_mysql_parameter_translation():
    assert (
        mysql_parameters("SELECT '?' AS text, id FROM projects WHERE id=? AND name LIKE '品牌%' ")
        == "SELECT '?' AS text, id FROM projects WHERE id=%s AND name LIKE '品牌%%' "
    )


def test_mysql_dates():
    row = format_row(
        {"created_at": datetime(2026, 9, 28, 16, 0), "collected_date": date(2026, 9, 28), "empty": None}
    )
    assert row == {"created_at": "2026-09-28 16:00:00", "collected_date": "2026-09-28", "empty": None}


def test_mysql_result_cursor():
    class Cursor:
        lastrowid = 1
        rowcount = 2
        description = True
        closed = False

        def fetchall(self):
            return [{"id": 1}, {"id": 2}]

        def close(self):
            self.closed = True

    cursor = Cursor()
    result = MySQLResult(cursor)
    assert cursor.closed and result.fetchone() == {"id": 1}
    assert result.fetchall() == [{"id": 2}]
    assert result.fetchone() is None


def test_persistent_superadmin(database_path):
    database = Database(database_path)
    create_admin(database, "仅用于测试的简单密码")
    with database.connect() as connection:
        user = connection.execute("SELECT * FROM users WHERE username=?", ("admin",)).fetchone()
        assert user["password_hash"].startswith("scrypt$")
        assert "仅用于测试的简单密码" not in user["password_hash"]
    with pytest.raises(RuntimeError, match="已存在"):
        create_admin(database, "不允许覆盖")
    with TestClient(create_app(database_path, api_token=""), headers={"X-GEO-Request": "1"}) as client:
        response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "仅用于测试的简单密码"}
        )
        assert response.status_code == 200 and response.json()["role"] == "superadmin"
        assert (
            client.post("/api/v1/projects", json={"name": "超级管理员验证", "brand": "星河"}).status_code
            == 201
        )
        with database.connect() as connection:
            connection.execute("UPDATE users SET enabled=0 WHERE username=?", ("admin",))
        assert client.get("/api/v1/projects").status_code == 401


def test_login_background_asset(client):
    assert client.get("/static/assets/code-rain.png").headers["content-type"] == "image/png"
    assert "code-rain-fall 7.5s" in client.get("/static/login-background.css").text
