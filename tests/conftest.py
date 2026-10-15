import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.auth import hash_password
from main import create_app


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "test.db"
    schema = Path(__file__).resolve().parents[1] / "sql" / "schema.sqlite.sql"
    with sqlite3.connect(path) as connection:
        connection.executescript(schema.read_text(encoding="utf-8"))
    return str(path)


@pytest.fixture
def client(database_path):
    app = create_app(
        database_path,
        api_token="",
        admin_username="研究员",
        admin_password_hash=hash_password("仅用于测试的密码123"),
    )
    with TestClient(app, headers={"X-GEO-Request": "1"}) as client:
        assert (
            client.post(
                "/api/v1/auth/login", json={"username": "研究员", "password": "仅用于测试的密码123"}
            ).status_code
            == 200
        )
        yield client


@pytest.fixture
def project(client):
    response = client.post(
        "/api/v1/projects",
        json={"name": "协作工具分析", "brand": "星河协作", "aliases": ["星河"], "competitors": ["云帆办公"]},
    )
    assert response.status_code == 201
    return response.json()
