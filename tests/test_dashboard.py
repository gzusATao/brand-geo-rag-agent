def test_dashboard_filter_and_date_basis(client, project):
    base = f"/api/v1/projects/{project['id']}"
    content = "question,answer,model,source,collected_date\n工具推荐,1. 推荐星河协作,模型甲,historical,2026-09-01\n工具推荐,推荐云帆办公,模型乙,historical,2026-09-02\n品牌适用人群,星河协作可进一步了解,模型甲,real,2026-09-02\n"
    batch = client.post(base + "/monitor-batches/import", json={"content": content}).json()
    data = client.get(base + "/monitor-dashboard").json()
    assert data["total"] == 3
    assert data["metrics"]["brands"][0]["mention_count"] == 2
    assert sum(data["rank_counts"].values()) == 3
    assert data["rank_counts"]["第一位"] == 1
    assert len(data["trend"]) == 2
    assert data["trend"][0]["date"] == "2026-09-01"
    assert data["trend"][0]["mention_rate"] == 1
    filtered = client.get(
        base + "/monitor-dashboard",
        params={
            "source": "historical",
            "question": "工具推荐",
            "model": "模型乙",
            "start_date": "2026-09-02",
            "end_date": "2026-09-02",
        },
    ).json()
    assert filtered["total"] == 1
    assert filtered["metrics"]["brands"][0]["mention_rate"] == 0
    assert filtered["models"][0]["model"] == "模型乙"
    assert client.get(base + "/monitor-dashboard", params={"start_date": "2026-09-03"}).json()["total"] == 0
    assert (
        client.get(
            base + "/monitor-dashboard", params={"start_date": "2026-09-03", "end_date": "2026-09-01"}
        ).status_code
        == 422
    )
    detail = client.get(
        f"/api/v1/monitor-batches/{batch['id']}/detail", params={"limit": 1, "offset": 1}
    ).json()
    assert detail["total_answers"] == 3 and len(detail["answers"]) == 1
    assert client.get("/api/v1/monitor-analyses", params={"start_date": "2099-01-01"}).json()["total"] == 0


def test_profile_read_scope_and_dashboard_batch_scope(client, project):
    base = f"/api/v1/projects/{project['id']}"
    doc = client.post(
        base + "/knowledge/documents",
        json={"title": "品牌背景资料", "source": "人工录入的虚构资料", "content": "星河协作为虚构协作工具。"},
    ).json()
    assert (
        client.get(base + f"/knowledge/documents/{doc['id']}").json()["content"] == "星河协作为虚构协作工具。"
    )
    other = client.post("/api/v1/projects", json={"name": "其他项目", "brand": "其他品牌"}).json()
    assert client.get(f"/api/v1/projects/{other['id']}/knowledge/documents/{doc['id']}").status_code == 404
    batch = client.post(
        base + "/monitor-batches/import",
        json={"content": "question,answer,model,source\n问题,星河协作,模拟器,mock\n"},
    ).json()
    assert (
        client.get(
            f"/api/v1/projects/{other['id']}/monitor-dashboard", params={"batch_id": batch["id"]}
        ).status_code
        == 404
    )
    data = client.get(base + "/monitor-dashboard", params={"batch_id": batch["id"]}).json()
    assert data["total"] == 1 and data["trend"][0]["date"] == data["answers"][0]["created_at"][:10]
