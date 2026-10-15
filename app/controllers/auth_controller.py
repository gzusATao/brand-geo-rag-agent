from fastapi import APIRouter, HTTPException, Request, Response

from app.apis.auth import LoginRequest, LogoutResponse, SessionResponse
from app.auth.auth import COOKIE_NAME, SESSION_SECONDS, check_browser_request

router = APIRouter(prefix="/auth", tags=["账号登录"])


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, request: Request, response: Response):
    check_browser_request(request)
    service = request.app.state.login
    token = service.login(
        payload.username, payload.password, request.client.host if request.client else "本机"
    )
    # 重新登录使当前浏览器旧会话失效，不把会话令牌暴露给 JavaScript。
    service.logout(request.cookies.get(COOKIE_NAME))
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=request.app.state.session_secure,
        samesite="strict",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    identity = service.session(token)
    return {"username": identity["username"], "role": identity["role"], "message": "登录成功"}


@router.get("/session", response_model=SessionResponse)
def session(request: Request, response: Response):
    service = request.app.state.login
    identity = service.session(request.cookies.get(COOKIE_NAME))
    if not identity:
        raise HTTPException(401, "登录已失效，请重新登录")
    response.headers["Cache-Control"] = "no-store"
    return {"username": identity["username"], "role": identity["role"], "message": "会话有效"}


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, response: Response):
    check_browser_request(request)
    request.app.state.login.logout(request.cookies.get(COOKIE_NAME))
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "已退出登录"}
