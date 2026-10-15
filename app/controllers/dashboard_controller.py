from datetime import date
from typing import Literal

from fastapi import APIRouter, Query, Request

from app.apis.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/projects/{project_id}/monitor-dashboard", response_model=DashboardResponse, tags=["监测看板"])
def monitor_dashboard(
    project_id: int,
    request: Request,
    source: Literal["mock", "historical", "real"] | None = None,
    batch_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    question: str = Query("", max_length=500),
    model: str = Query("", max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return DashboardService(request.app.state.database).get(
        project_id, source, batch_id, start_date, end_date, question, model, limit, offset
    )
