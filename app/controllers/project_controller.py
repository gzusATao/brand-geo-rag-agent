from datetime import date
from typing import Literal

from fastapi import APIRouter, Query, Request

from app.apis.project import (
    MonitorProjectCreate,
    MonitorProjectPage,
    ProjectCreate,
    ProjectNameUpdate,
    ProjectResponse,
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("/monitor-projects", response_model=ProjectResponse, status_code=201, tags=["监测项目"])
def create_monitor_project(payload: MonitorProjectCreate, request: Request):
    return ProjectService(request.app.state.database).create(payload)


@router.get("/monitor-projects", response_model=MonitorProjectPage, tags=["监测项目"])
def monitor_projects(
    request: Request,
    name: str = "",
    brand: str = "",
    status: Literal["draft", "pending", "running", "completed", "failed"] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return ProjectService(request.app.state.database).page(
        name, brand, status, start_date, end_date, page, page_size
    )


@router.patch("/projects/{project_id}", response_model=ProjectResponse, tags=["监测项目"])
def rename_project(project_id: int, payload: ProjectNameUpdate, request: Request):
    return ProjectService(request.app.state.database).rename(project_id, payload.name)


@router.post("/projects", response_model=ProjectResponse, status_code=201, tags=["项目"])
def create_project(payload: ProjectCreate, request: Request):
    return ProjectService(request.app.state.database).create(payload)


@router.get("/projects", response_model=list[ProjectResponse], tags=["项目"])
def list_projects(request: Request):
    return ProjectService(request.app.state.database).list()


@router.get("/projects/{project_id}", response_model=ProjectResponse, tags=["项目"])
def get_project(project_id: int, request: Request):
    return ProjectService(request.app.state.database).get(project_id)


@router.post(
    "/projects/{project_id}/questions", response_model=QuestionResponse, status_code=201, tags=["问句"]
)
def create_question(project_id: int, payload: QuestionCreate, request: Request):
    return ProjectService(request.app.state.database).add_question(project_id, payload.text)


@router.get("/projects/{project_id}/questions", response_model=list[QuestionResponse], tags=["问句"])
def list_questions(project_id: int, request: Request):
    return ProjectService(request.app.state.database).questions(project_id)


@router.patch(
    "/projects/{project_id}/questions/{question_id}", response_model=QuestionResponse, tags=["问句"]
)
def update_question(project_id: int, question_id: int, payload: QuestionUpdate, request: Request):
    return ProjectService(request.app.state.database).update_question(
        project_id, question_id, payload.enabled
    )
