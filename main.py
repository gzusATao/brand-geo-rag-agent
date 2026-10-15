import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.apis.base import HealthResponse
from app.auth.auth import COOKIE_NAME, LoginService, authorize
from app.controllers import (
    agent_chat_controller,
    article_task_controller,
    auth_controller,
    dashboard_controller,
    knowledge_base_controller,
    project_controller,
    task_controller,
)
from app.libs.database import Database
from app.services.task_service import TaskService
from app.services.agent_chat_service import AgentChatService

load_dotenv(Path(__file__).parent / ".env")


def create_app(database_path=None, api_token=None, admin_username=None, admin_password_hash=None):
    database = Database(database_path)

    @asynccontextmanager
    async def lifespan(application):
        database.check_schema()
        TaskService(database).interrupt_incomplete()
        yield

    application = FastAPI(
        title="品牌GEO分析与优化原型",
        version="0.1.0",
        lifespan=lifespan,
        description="单机单用户原型，包括模拟监测、词面检索、固定摘录工作流及受控的百炼多智能体对话；不提供公共平台自动采集或发布。",
    )
    application.state.database = database
    application.state.agent_chat = AgentChatService(database)
    application.state.login = LoginService(
        os.getenv("GEO_ADMIN_USERNAME", "") if admin_username is None else admin_username,
        os.getenv("GEO_ADMIN_PASSWORD_HASH", "") if admin_password_hash is None else admin_password_hash,
        database=database if admin_username is None and admin_password_hash is None else None,
    )
    application.state.session_secure = os.getenv("GEO_SESSION_SECURE", "0") == "1"
    application.state.api_token = os.getenv("GEO_API_TOKEN", "") if api_token is None else api_token
    if not application.state.api_token.isascii():
        raise ValueError("访问令牌必须使用ASCII字符，以符合HTTP请求头格式")
    application.include_router(auth_controller.router, prefix="/api/v1")
    for controller in (
        agent_chat_controller,
        dashboard_controller,
        project_controller,
        task_controller,
        knowledge_base_controller,
        article_task_controller,
    ):
        application.include_router(controller.router, prefix="/api/v1", dependencies=[Depends(authorize)])
    static = Path(__file__).parent / "app" / "templates"
    application.mount("/static", StaticFiles(directory=static), name="static")

    @application.middleware("http")
    async def revalidate_static_assets(request: Request, call_next):
        response = await call_next(request)
        # 本地开发没有资源指纹构建；每次重新验证，避免新监控脚本调用旧版公共脚本。
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    @application.get("/", include_in_schema=False)
    def index(request: Request):
        if not application.state.login.session(request.cookies.get(COOKIE_NAME)):
            return RedirectResponse("/login", status_code=303)
        return FileResponse(static / "index.html", headers={"Cache-Control": "no-store"})

    @application.get("/login", include_in_schema=False)
    def login_page(request: Request):
        if application.state.login.session(request.cookies.get(COOKIE_NAME)):
            return RedirectResponse("/", status_code=303)
        return FileResponse(static / "login.html", headers={"Cache-Control": "no-store"})

    @application.get("/health", response_model=HealthResponse, tags=["服务状态"])
    def health():
        return {"status": "运行正常", "version": "0.1.0"}

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exception: RequestValidationError):
        fields = [".".join(str(part) for part in error["loc"]) for error in exception.errors()]
        # 不回显输入与第三方英文验证文本，避免把敏感资料带入失败响应。
        return JSONResponse(
            status_code=422, content={"detail": "请求参数不符合要求，请检查字段：" + "、".join(fields)}
        )

    return application


app = create_app()
