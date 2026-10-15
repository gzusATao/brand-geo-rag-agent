from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.apis.article_task import OptimizationRequest, OptimizationResponse, ReviewRequest
from app.services.article_task_service import ArticleTaskService

router = APIRouter()


@router.post(
    "/projects/{project_id}/optimization-runs",
    response_model=OptimizationResponse,
    status_code=201,
    tags=["辅助优化"],
)
def optimize(project_id: int, payload: OptimizationRequest, request: Request):
    return ArticleTaskService(request.app.state.database).create(project_id, payload)


@router.get(
    "/projects/{project_id}/optimization-runs", response_model=list[OptimizationResponse], tags=["辅助优化"]
)
def list_optimizations(project_id: int, request: Request):
    return ArticleTaskService(request.app.state.database).list(project_id)


@router.get("/optimization-runs/{run_id}", response_model=OptimizationResponse, tags=["辅助优化"])
def get_optimization(run_id: int, request: Request):
    return ArticleTaskService(request.app.state.database).get(run_id)


@router.post("/optimization-runs/{run_id}/review", response_model=OptimizationResponse, tags=["辅助优化"])
def review(run_id: int, payload: ReviewRequest, request: Request):
    return ArticleTaskService(request.app.state.database).review(run_id, payload)


@router.get("/optimization-runs/{run_id}/export", tags=["辅助优化"])
def export(run_id: int, request: Request):
    content = ArticleTaskService(request.app.state.database).export(run_id)
    return Response(
        content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="draft-{run_id}.md"'},
    )
