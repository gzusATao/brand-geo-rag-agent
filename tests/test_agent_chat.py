import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException

from app.apis.agent_chat import AgentChatRequest, GroundedAnswer, SupervisorPlan
from app.libs.qwen_client import QwenClient, valid_qwen_endpoint


def test_unconfigured_model_is_explicit_and_does_not_create_session(client, project):
    service = client.app.state.agent_chat
    service.model.key = ""
    config = client.get("/api/v1/agent-chat/config").json()
    assert not config["configured"]
    response = client.post(f"/api/v1/projects/{project['id']}/agent-chat", json={"message": "分析品牌"})
    assert response.status_code == 503
    assert "配置" in response.json()["detail"]
    assert not service.sessions and not service.runs


def test_multi_agent_parallel_tools_citations_history_and_project_isolation(client, project, monkeypatch):
    base = f"/api/v1/projects/{project['id']}"
    client.post(
        base + "/knowledge/documents",
        json={
            "title": "星河协作介绍",
            "source": "人工虚构测试资料",
            "content": "星河协作提供项目管理和文档协作。",
        },
    )
    hit = client.post(base + "/knowledge/retrieve", json={"query": "星河协作", "top_k": 1}).json()[0]
    service = client.app.state.agent_chat
    monkeypatch.setattr(service.model, "configured", lambda: True)
    seen = []

    async def complete(system, context, schema):
        seen.append(context)
        if schema is SupervisorPlan:
            return SupervisorPlan(intent="analysis", query="星河协作", agents=["rag", "tool"])
        if "专业结果" in context:
            assert set(context["专业结果"]) == {"rag", "tool"}
            assert context["专业结果"]["tool"]["真实回答"]["sample_count"] == 0
        return GroundedAnswer(
            answer="【接口模拟测试】星河协作提供项目管理功能，尚无真实效果样本。",
            citation_ids=[hit["chunk_id"]],
        )

    monkeypatch.setattr(service.model, "complete", complete)
    submitted = client.post(base + "/agent-chat", json={"message": "分析品牌并参考企业资料"})
    assert submitted.status_code == 202
    run = submitted.json()
    result = client.get(base + "/agent-chat/" + run["id"]).json()
    assert result["status"] == "completed"
    assert all(step["status"] == "completed" for step in result["trace"])
    assert result["citations"][0]["chunk_id"] == hit["chunk_id"]
    assert "T" not in result["created_at"]
    history = client.get(base + "/agent-sessions/" + run["session_id"]).json()
    assert len(history["messages"]) == 2
    assert client.get(f"/api/v1/projects/{project['id'] + 999}/agent-chat/{run['id']}").status_code == 404
    second = client.post(base + "/agent-chat", json={"message": "继续说明", "session_id": run["session_id"]})
    assert second.status_code == 202
    assert len(seen[3]["近期对话"]) == 2
    assert client.get(base + "/agent-chat/" + second.json()["id"]).json()["status"] == "completed"


def test_invalid_citation_fails_without_polluting_memory(client, project, monkeypatch):
    service = client.app.state.agent_chat
    monkeypatch.setattr(service.model, "configured", lambda: True)

    async def complete(system, context, schema):
        if schema is SupervisorPlan:
            return SupervisorPlan(intent="knowledge", query="星河协作", agents=["rag"])
        return GroundedAnswer(answer="这是无法核对来源的回答", citation_ids=[99999])

    monkeypatch.setattr(service.model, "complete", complete)
    base = f"/api/v1/projects/{project['id']}"
    run = client.post(base + "/agent-chat", json={"message": "介绍产品"}).json()
    result = client.get(base + "/agent-chat/" + run["id"]).json()
    assert result["status"] == "failed" and result["answer"] is None
    assert "不存在" in result["error"]
    assert not any(step["status"] in {"pending", "running"} for step in result["trace"])
    assert client.get(base + "/agent-sessions/" + run["session_id"]).json()["messages"] == []


def test_busy_session_and_call_limits_are_enforced(client, project, monkeypatch):
    service = client.app.state.agent_chat
    monkeypatch.setattr(service.model, "configured", lambda: True)
    first = service.submit(project["id"], AgentChatRequest(message="第一次分析"))
    with pytest.raises(HTTPException) as busy:
        service.submit(project["id"], AgentChatRequest(message="重复发送", session_id=first["session_id"]))
    assert busy.value.status_code == 409
    service.submit(project["id"], AgentChatRequest(message="第二个会话"))
    with pytest.raises(HTTPException) as capacity:
        service.submit(project["id"], AgentChatRequest(message="第三个任务"))
    assert capacity.value.status_code == 429


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://dashscope.aliyuncs.com/v1",
        "https://example.com/v1",
        "https://bucket.oss-cn-beijing.aliyuncs.com/v1",
        "https://dashscope.aliyuncs.com@evil.example/v1",
    ],
)
def test_model_credentials_are_not_sent_to_other_endpoints(endpoint):
    assert not valid_qwen_endpoint(endpoint)


def test_qwen_http_contract_is_json_validated_and_redacts_provider_errors(monkeypatch):
    monkeypatch.setenv("GEO_QWEN_API_KEY", "test-only-key")
    model = QwenClient()
    original = httpx.AsyncClient
    requests = []

    def transport(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {"answer": "测试回复", "citation_ids": []}, ensure_ascii=False
                            )
                        },
                    }
                ]
            },
        )

    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(transport))
    )
    reply = asyncio.run(model.complete("请返回中文 JSON", {"问题": "你好"}, GroundedAnswer))
    assert reply.answer == "测试回复"
    assert requests[0]["response_format"] == {"type": "json_object"}
    assert requests[0]["enable_thinking"] is False

    def failure(request):
        return httpx.Response(401, text="不得回显的供应商密钥和企业内容")

    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(failure))
    )
    with pytest.raises(HTTPException) as error:
        asyncio.run(model.complete("中文 JSON", {}, GroundedAnswer))
    assert "鉴权失败" in error.value.detail and "供应商" not in error.value.detail
