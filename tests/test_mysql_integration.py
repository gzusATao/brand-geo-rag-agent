"""显式启用的真实MySQL联调，所有业务样本在同一事务中回滚，不清空任何表。"""

import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.libs.database import Database, MySQLConnection
from main import create_app

pytestmark = pytest.mark.skipif(
    os.getenv("GEO_TEST_MYSQL") != "1", reason="真实MySQL联调需显式启用并提供测试登录密码"
)


def test_mysql_workflow():
    database = Database()
    assert database.engine == "mysql"
    database.check_schema()
    with database.connect() as connection:
        rows = connection.execute(
            "SELECT TABLE_NAME AS table_name,COLUMN_NAME AS column_name "
            "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() "
            "ORDER BY TABLE_NAME,ORDINAL_POSITION"
        ).fetchall()
        tables = {}
        for row in rows:
            tables.setdefault(row["table_name"], []).append(row["column_name"])
        assert len(tables) == 9
        assert all(columns[-2:] == ["created_at", "updated_at"] for columns in tables.values())

    raw = database.mysql_connect()

    class TransactionDatabase:
        integrity_errors = database.integrity_errors

        @contextmanager
        def connect(self):
            # 测试请求顺序执行，共享未提交事务；管理员认证仍从正式连接读取。
            yield MySQLConnection(raw)

    app = create_app()
    app.state.database = TransactionDatabase()
    try:
        with TestClient(app, headers={"X-GEO-Request": "1"}) as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": os.environ["GEO_TEST_ADMIN_PASSWORD"]},
            )
            assert response.status_code == 200 and response.json()["role"] == "superadmin"
            project = client.post(
                "/api/v1/monitor-projects",
                json={
                    "name": "事务内联调样本",
                    "brand": "星河协作",
                    "initial_questions": ["品牌适合哪些场景？"],
                },
            )
            assert project.status_code == 201
            path = f"/api/v1/projects/{project.json()['id']}"
            assert "T" not in project.json()["created_at"]
            question = client.post(path + "/questions", json={"text": "哪些协作工具适合小团队？"})
            assert question.status_code == 201
            assert (
                client.post(path + "/questions", json={"text": "哪些协作工具适合小团队？"}).status_code == 409
            )
            question_path = path + f"/questions/{question.json()['id']}"
            assert client.patch(question_path, json={"enabled": False}).status_code == 200
            assert client.patch(question_path, json={"enabled": False}).status_code == 200
            assert client.patch(question_path, json={"enabled": True}).status_code == 200
            batch = client.post(
                path + "/monitor-batches/mock", json={"question_ids": [question.json()["id"]]}
            )
            assert batch.status_code == 202
            assert client.get(f"/api/v1/monitor-batches/{batch.json()['id']}").json()["status"] == "completed"
            assert client.get(path + "/metrics?source=mock").json()["sample_count"] == 1
            assert client.get(path + "/monitor-dashboard?source=mock").json()["total"] == 1
            detail = client.get(f"/api/v1/monitor-batches/{batch.json()['id']}/detail").json()
            assert detail["total_answers"] == 1 and len(detail["answers"]) == 1
            library = client.get(
                "/api/v1/monitor-projects", params={"name": "事务内联调", "status": "completed"}
            ).json()
            assert library["total"] == 1 and library["items"][0]["question_count"] == 2
            analysis = client.get(
                "/api/v1/monitor-analyses", params={"question": "小团队", "source": "mock"}
            ).json()
            # 正式库可存在用户同问句记录，验证本事务批次出现，不假设库为空。
            assert any(item["id"] == batch.json()["id"] for item in analysis["items"])
            assert client.patch(path, json={"name": "事务内联调已修改"}).status_code == 200
            csv = "question,answer,model,source,collected_date\n问题,推荐星河协作,人工测试模型,mock,2026-09-28\n"
            assert client.post(path + "/monitor-batches/import", json={"content": csv}).status_code == 201
            answers = client.get(path + "/answers").json()
            assert answers[0]["collected_date"] == "2026-09-28" and "T" not in answers[0]["created_at"]
            document = client.post(
                path + "/knowledge/documents",
                json={
                    "title": "联调虚构资料",
                    "source": "事务回滚测试，不作为论文样本",
                    "content": "星河协作支持团队文档协作。",
                },
            )
            assert document.status_code == 201
            assert (
                client.get(path + f"/knowledge/documents/{document.json()['id']}").json()["content"]
                == "星河协作支持团队文档协作。"
            )
            assert client.post(path + "/knowledge/retrieve", json={"query": "团队文档协作"}).json()
            run = client.post(path + "/optimization-runs", json={"query": "团队文档协作"})
            assert run.status_code == 201
            run_path = f"/api/v1/optimization-runs/{run.json()['id']}"
            assert (
                client.post(
                    run_path + "/review", json={"status": "approved", "note": "仅验证MySQL流程"}
                ).status_code
                == 200
            )
            assert client.get(run_path + "/export").status_code == 200
            assert client.post("/api/v1/auth/logout").status_code == 200
            assert client.get("/api/v1/projects").status_code == 401
    finally:
        raw.rollback()
        raw.close()
