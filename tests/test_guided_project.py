def test_create_project_and_initial_questions_atomically(client):
    response = client.post(
        "/api/v1/monitor-projects",
        json={
            "name": "入门体验",
            "brand": "星河协作",
            "initial_questions": ["有哪些协作工具？", "小团队怎么选？"],
        },
    )
    assert response.status_code == 201
    project_id = response.json()["id"]
    questions = client.get(f"/api/v1/projects/{project_id}/questions").json()
    assert len(questions) == 2 and all(question["enabled"] for question in questions)
    batch = client.post(
        f"/api/v1/projects/{project_id}/monitor-batches/mock",
        json={"question_ids": [q["id"] for q in questions]},
    )
    assert batch.status_code == 202
    metrics = client.get(
        f"/api/v1/projects/{project_id}/metrics", params={"batch_id": batch.json()["id"], "source": "mock"}
    ).json()
    assert metrics["sample_count"] == 2


def test_invalid_initial_questions_leave_no_project(client):
    for questions in (["问题？", "问题!"], ["!!!"], ["问" * 501]):
        response = client.post(
            "/api/v1/monitor-projects",
            json={"name": "不能留下空项目", "brand": "星河", "initial_questions": questions},
        )
        assert response.status_code == 422
    assert client.get("/api/v1/projects").json() == []
