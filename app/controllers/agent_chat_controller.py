from fastapi import APIRouter, BackgroundTasks, Request

from app.apis.agent_chat import AgentChatRequest, AgentChatRun, AgentModelStatus, AgentSession

router = APIRouter()


@router.get("/agent-chat/config", response_model=AgentModelStatus, tags=["多智能体对话"])
def model_status(request: Request):
    return request.app.state.agent_chat.config()


@router.post(
    "/projects/{project_id}/agent-chat", response_model=AgentChatRun, status_code=202, tags=["多智能体对话"]
)
def send_message(project_id: int, payload: AgentChatRequest, background: BackgroundTasks, request: Request):
    service = request.app.state.agent_chat
    run = service.submit(project_id, payload)
    background.add_task(service.execute, run["id"], payload.message)
    return run


@router.get("/projects/{project_id}/agent-chat/{run_id}", response_model=AgentChatRun, tags=["多智能体对话"])
def run_status(project_id: int, run_id: str, request: Request):
    return request.app.state.agent_chat.get(project_id, run_id)


@router.get(
    "/projects/{project_id}/agent-sessions/{session_id}", response_model=AgentSession, tags=["多智能体对话"]
)
def session_history(project_id: int, session_id: str, request: Request):
    return request.app.state.agent_chat.session(project_id, session_id)
