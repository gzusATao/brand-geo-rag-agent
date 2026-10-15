from datetime import date
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Query, Request

from app.apis.task import (
    AnalysisDetail,
    AnalysisPage,
    AnswerResponse,
    BatchResponse,
    CsvImportRequest,
    MetricsResponse,
    MockBatchRequest,
)
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/monitor-batches/{batch_id}/detail", response_model=AnalysisDetail, tags=["监测"])
def analysis_detail(
    batch_id: int, request: Request, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
):
    return TaskService(request.app.state.database).detail(batch_id, limit, offset)


@router.get("/monitor-analyses", response_model=AnalysisPage, tags=["监测"])
def list_analyses(
    request: Request,
    brand: str = "",
    question: str = "",
    status: Literal["pending", "running", "completed", "failed"] | None = None,
    source: Literal["mock", "historical", "real", "mixed"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
):
    return TaskService(request.app.state.database).analysis_page(
        brand, question, status, source, page, page_size, start_date, end_date
    )


@router.post(
    "/projects/{project_id}/monitor-batches/import",
    response_model=BatchResponse,
    status_code=201,
    tags=["监测"],
)
def import_answers(project_id: int, payload: CsvImportRequest, request: Request):
    return TaskService(request.app.state.database).import_csv(project_id, payload.content)


@router.post(
    "/projects/{project_id}/monitor-batches/mock",
    response_model=BatchResponse,
    status_code=202,
    tags=["监测"],
)
def mock_monitor(
    project_id: int, payload: MockBatchRequest, background_tasks: BackgroundTasks, request: Request
):
    service = TaskService(request.app.state.database)
    batch, project, snapshots = service.create_mock(project_id, payload.question_ids)
    background_tasks.add_task(service.run_mock, batch["id"], project, snapshots)
    return batch


@router.get("/monitor-batches/{batch_id}", response_model=BatchResponse, tags=["监测"])
def get_batch(batch_id: int, request: Request):
    return TaskService(request.app.state.database).batch(batch_id)


@router.get("/projects/{project_id}/monitor-batches", response_model=list[BatchResponse], tags=["监测"])
def list_batches(project_id: int, request: Request):
    return TaskService(request.app.state.database).batches(project_id)


@router.get("/projects/{project_id}/answers", response_model=list[AnswerResponse], tags=["监测"])
def list_answers(
    project_id: int,
    request: Request,
    source: Literal["mock", "historical", "real"] | None = None,
    batch_id: int | None = None,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return TaskService(request.app.state.database).answers(project_id, source, batch_id, limit, offset)


@router.get("/projects/{project_id}/metrics", response_model=MetricsResponse, tags=["监测"])
def get_metrics(
    project_id: int,
    request: Request,
    source: Literal["mock", "historical", "real"] | None = None,
    batch_id: int | None = None,
):
    return TaskService(request.app.state.database).metrics(project_id, source, batch_id)
