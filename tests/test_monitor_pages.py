import re


def test_workspace_uses_original_skipper_avatar(client):
    html = client.get("/").text
    avatar_url = "/static/assets/agents/penguin-team-reference.png"
    assert f'src="{avatar_url}"' in html
    assert '<span class="brand-icon">G</span>' not in html
    assert 'aria-label="GEO 品牌研究工作台首页"' in html
    assert 'alt="老大 Skipper，用户原图头像"' in html
    assert 'style="--portrait-x:237px;--portrait-y:147px"' in html
    assert "/static/assets/agents/commander-avatar.png" not in html
    response = client.get(avatar_url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_home_agent_cards_use_user_supplied_portraits(client):
    script = client.get("/static/guide.js").text
    assert "${homeAgentPortrait(agent)}<h4>" in script
    assert "${homeAgentPortrait(agent,true)}" in script
    assert 'tool:{name:"菜鸟",english:"Private"' in script
    assert 'summary:{name:"瑞科",english:"Rico"' in script
    response = client.get("/static/assets/agents/penguin-team-reference.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_monitor_assets_revalidate_as_one_version(client):
    html = client.get("/").text
    versions = re.findall(r'/static/(?:[a-z]+\.js|[a-z]+\.css)\?v=([^" ]+)', html)
    assert len(versions) == 9 and len(set(versions)) == 1
    for asset in ("app.js", "monitor.js", "guide.js", "monitor.css", "console.js", "dashboard.js"):
        response = client.get(f"/static/{asset}?v={versions[0]}")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"
    script = client.get("/static/app.js").text
    for name in ("single", "library", "history", "setup"):
        assert name + ":[" in script


def test_workspace_action_and_filter_accessibility(client):
    app_script = client.get("/static/app.js").text
    guide_script = client.get("/static/guide.js").text
    dashboard_script = client.get("/static/dashboard.js").text
    assert 'setAttribute("aria-busy","true")' in app_script
    assert "workspace-action-finished" in app_script
    assert "updateCollectControls" in guide_script
    assert 'setAttribute("aria-describedby","csv-selection")' in guide_script
    assert 'setAttribute("aria-pressed"' in dashboard_script
    assert "统计更新失败，当前仍是上次结果" in dashboard_script
    assert 'disabled=!data.total' in dashboard_script


def test_project_library_filters_and_settings(client, project):
    url = "/api/v1/monitor-projects"
    result = client.get(url, params={"name": "协作", "status": "draft", "page_size": 1}).json()
    assert result["total"] == 1
    assert result["items"][0]["question_count"] == 0
    assert client.get(url, params={"brand": "不存在"}).json()["total"] == 0
    assert client.get(url, params={"page": 2, "page_size": 1}).json()["items"] == []
    assert client.get(url, params={"start_date": "2026-10-01", "end_date": "2026-09-01"}).status_code == 422
    renamed = client.patch(f"/api/v1/projects/{project['id']}", json={"name": "品牌研究一期"})
    assert renamed.status_code == 200
    assert renamed.json()["brand"] == project["brand"]
    assert renamed.json()["name"] == "品牌研究一期"
    assert (
        client.patch(
            f"/api/v1/projects/{project['id']}", json={"name": "修改", "brand": "别的品牌"}
        ).status_code
        == 422
    )


def test_single_analysis_and_batch_filter(client, project):
    base = f"/api/v1/projects/{project['id']}"
    question = client.post(base + "/questions", json={"text": "协作工具推荐？"}).json()
    batch = client.post(base + "/monitor-batches/mock", json={"question_ids": [question["id"]]}).json()
    page = client.get(
        "/api/v1/monitor-analyses", params={"question": "协作", "source": "mock", "status": "completed"}
    ).json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == batch["id"]
    assert page["items"][0]["brand"] == project["brand"]
    assert page["items"][0]["total"] == 1
    assert "T" not in page["items"][0]["created_at"]
    assert client.get("/api/v1/monitor-analyses", params={"source": "real"}).json()["total"] == 0
    library = client.get("/api/v1/monitor-projects", params={"status": "completed"}).json()
    assert library["total"] == 1
    assert library["items"][0]["question_count"] == 1
    assert (
        client.get(base + "/metrics", params={"batch_id": batch["id"], "source": "mock"}).json()[
            "sample_count"
        ]
        == 1
    )
