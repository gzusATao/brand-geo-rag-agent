import re
import sqlite3

from fastapi.testclient import TestClient

from main import create_app


def test_health_and_ui(client):
    assert client.get("/health").json()["status"] == "运行正常"
    assert "品牌GEO" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200


def test_project_validation(client):
    assert client.post("/api/v1/projects", json={"name": " ", "brand": "星河"}).status_code == 422
    assert (
        client.post(
            "/api/v1/projects", json={"name": "测试", "brand": "星河", "aliases": ["星河"]}
        ).status_code
        == 422
    )
    assert client.get("/api/v1/projects/999").json()["detail"] == "品牌项目不存在"


def test_question_dedup_and_disable(client, project):
    path = f"/api/v1/projects/{project['id']}"
    question = client.post(path + "/questions", json={"text": "推荐哪些 工具？"}).json()
    assert client.post(path + "/questions", json={"text": "推荐哪些工具?"}).status_code == 409
    assert client.post(path + "/questions", json={"text": "？！"}).status_code == 422
    assert client.patch(path + f"/questions/{question['id']}", json={"enabled": False}).status_code == 200
    assert (
        client.post(path + "/monitor-batches/mock", json={"question_ids": [question["id"]]}).status_code
        == 422
    )


def test_mock_batch_and_metrics(client, project):
    path = f"/api/v1/projects/{project['id']}"
    ids = [
        client.post(path + "/questions", json={"text": f"场景{i}有哪些工具？"}).json()["id"] for i in range(3)
    ]
    response = client.post(path + "/monitor-batches/mock", json={"question_ids": ids})
    assert response.status_code == 202
    batch = client.get(f"/api/v1/monitor-batches/{response.json()['id']}").json()
    assert batch["status"] == "completed" and batch["completed"] == 3
    metrics = client.get(path + "/metrics?source=mock").json()
    assert metrics["sample_count"] == 3
    assert metrics["brands"][0]["mention_count"] == 2
    assert metrics["brands"][0]["recommendation_count"] == 1
    assert metrics["brands"][0]["rank_distribution"] == {"1": 1}
    assert client.get(path + "/metrics?source=real").json()["sample_count"] == 0
    answers = client.get(path + "/answers").json()
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", row["created_at"]) for row in answers)
    assert all(row["collected_date"] is None for row in answers)


def test_csv_atomic_validation(client, project):
    path = f"/api/v1/projects/{project['id']}"
    content = "question,answer,model,source\n问题一,推荐星河协作,历史模型,historical\n问题二,未知,模型,伪造\n"
    assert client.post(path + "/monitor-batches/import", json={"content": content}).status_code == 422
    assert client.get(path + "/monitor-batches").json() == []
    assert client.get(path + "/metrics").json()["sample_count"] == 0


def test_csv_source_date_and_batch_filter(client, project):
    path = f"/api/v1/projects/{project['id']}"
    content = '\ufeffquestion,answer,model,source,collected_date\n问题一,"推荐星河协作，不推荐云帆办公。",历史模型,historical,2026-09-28\n问题二,推荐云帆办公,模拟模型,mock,\n'
    batch = client.post(path + "/monitor-batches/import", json={"content": content}).json()
    assert batch["source"] == "mixed"
    assert client.get(path + f"/metrics?batch_id={batch['id']}").json()["sample_count"] == 2
    assert client.get(path + "/metrics?source=historical").json()["brands"][0]["recommendation_rate"] == 1.0
    answers = client.get(path + "/answers?source=historical").json()
    assert answers[0]["collected_date"] == "2026-09-28"
    assert answers[0]["extraction"][1]["recommended"] is False
    bad = content.replace("2026-09-28", "2026-9-28")
    assert client.post(path + "/monitor-batches/import", json={"content": bad}).status_code == 422


def test_project_boundaries(client, project):
    first = f"/api/v1/projects/{project['id']}"
    other = client.post("/api/v1/projects", json={"name": "另一个项目", "brand": "另一品牌"}).json()
    second = f"/api/v1/projects/{other['id']}"
    question = client.post(first + "/questions", json={"text": "推荐哪个工具？"}).json()
    assert (
        client.post(second + "/monitor-batches/mock", json={"question_ids": [question["id"]]}).status_code
        == 422
    )
    assert client.patch(second + f"/questions/{question['id']}", json={"enabled": False}).status_code == 404
    client.post(
        first + "/knowledge/documents",
        json={"title": "团队协作说明", "source": "虚构资料", "content": "星河协作支持团队文档协作。"},
    )
    assert client.post(second + "/knowledge/retrieve", json={"query": "团队协作"}).json() == []


def test_knowledge_optimization_and_review(client, project, database_path):
    path = f"/api/v1/projects/{project['id']}"
    document = client.post(
        path + "/knowledge/documents",
        json={"title": "产品说明", "source": "虚构品牌设定", "content": "星河协作支持团队文档协作。"},
    ).json()
    assert document["chunk_count"] == 1
    query = {"query": "团队文档协作", "top_k": 3}
    hits = client.post(path + "/knowledge/retrieve", json=query).json()
    assert hits[0]["document_id"] == document["id"] and hits[0]["score"] > 0
    run = client.post(path + "/optimization-runs", json=query).json()
    assert run["mode"] == "固定工具工作流演示" and "暂无非模拟" in run["diagnosis"]
    assert len(run["trace"]) == 3 and run["citations"] == hits
    assert client.get(f"/api/v1/optimization-runs/{run['id']}/export").status_code == 409
    reviewed = client.post(
        f"/api/v1/optimization-runs/{run['id']}/review",
        json={"status": "approved", "note": "已核对虚构资料", "draft": "人工核对后的草稿"},
    ).json()
    assert reviewed["review_status"] == "approved"
    assert client.get(f"/api/v1/optimization-runs/{run['id']}/export").text == "人工核对后的草稿"
    client.post(
        f"/api/v1/optimization-runs/{run['id']}/review", json={"status": "rejected", "note": "需要补充证据"}
    )
    assert client.get(f"/api/v1/optimization-runs/{run['id']}/export").status_code == 409
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 2


def test_no_evidence_is_explicit(client, project):
    run = client.post(
        f"/api/v1/projects/{project['id']}/optimization-runs", json={"query": "不存在的事实"}
    ).json()
    assert run["citations"] == [] and "证据不足" in run["draft"]


def test_auth(database_path):
    with TestClient(create_app(database_path, api_token="test-access-token")) as secured:
        assert secured.get("/api/v1/projects").status_code == 401
        assert secured.get("/api/v1/projects", headers={"X-API-Key": "invalid-token"}).status_code == 401
        assert secured.get("/api/v1/projects", headers={"X-API-Key": "test-access-token"}).status_code == 200


def test_openapi_descriptions(client):
    schema = client.get("/openapi.json").json()
    for model in schema["components"]["schemas"].values():
        if model.get("title") in {"HTTPValidationError", "ValidationError"}:
            continue
        for field in model.get("properties", {}).values():
            assert re.search(r"[\u4e00-\u9fff]", field.get("description", ""))


def test_restart_marks_incomplete(database_path):
    with TestClient(
        create_app(database_path, api_token="restart-test"), headers={"X-API-Key": "restart-test"}
    ) as client:
        project = client.post("/api/v1/projects", json={"name": "重启测试", "brand": "星河"}).json()
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO batches(project_id,source,status,total,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (project["id"], "mock", "pending", 1, "2026-09-28 10:00:00", "2026-09-28 10:00:00"),
        )
    with TestClient(
        create_app(database_path, api_token="restart-test"), headers={"X-API-Key": "restart-test"}
    ) as client:
        batch = client.get(f"/api/v1/projects/{project['id']}/monitor-batches").json()[0]
        assert batch["status"] == "failed" and "重启" in batch["error"]
