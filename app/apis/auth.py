from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100, description="管理员登录账号")
    password: str = Field(min_length=1, max_length=256, description="管理员登录密码，不去除首尾空格")


class SessionResponse(BaseModel):
    username: str = Field(description="当前登录的管理员账号")
    role: str = Field(description="当前账号角色，superadmin表示具有全部工作台业务权限的超级管理员")
    message: str = Field(description="登录或会话查询结果的中文说明")


class LogoutResponse(BaseModel):
    message: str = Field(description="退出登录操作结果的中文说明")
