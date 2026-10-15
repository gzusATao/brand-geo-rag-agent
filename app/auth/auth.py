import hashlib
import secrets
import time
from threading import Lock
from urllib.parse import urlsplit

from fastapi import HTTPException, Request

COOKIE_NAME = "geo_session"
SESSION_SECONDS = 8 * 60 * 60


def authorize(request: Request):
    expected = request.app.state.api_token
    supplied = request.headers.get("X-API-Key", "")
    if expected and secrets.compare_digest(supplied.encode(), expected.encode()):
        return
    identity = request.app.state.login.session(request.cookies.get(COOKIE_NAME))
    if not identity:
        raise HTTPException(401, "登录已失效，请重新登录")
    if identity["role"] != "superadmin":
        raise HTTPException(403, "当前账号没有超级管理员权限")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        check_browser_request(request)


def check_browser_request(request: Request):
    # 自定义请求头与同源校验共同阻止跨站表单提交；不开放跨源 CORS。
    origin = request.headers.get("origin")
    if request.headers.get("X-GEO-Request") != "1" or (
        origin and urlsplit(origin).netloc != request.url.netloc
    ):
        raise HTTPException(403, "请求来源校验失败，请刷新页面后重试")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


class LoginService:
    def __init__(self, username, password_hash, database=None):
        self.username = username
        self.password_hash = password_hash
        self.database = database
        self.sessions = {}
        self.identities = {}
        self.failures = {}
        self.lock = Lock()
        if password_hash:
            try:
                algorithm, salt, digest = password_hash.split("$")
                if (
                    algorithm != "scrypt"
                    or len(bytes.fromhex(salt)) != 16
                    or len(bytes.fromhex(digest)) != 64
                ):
                    raise ValueError
            except ValueError as error:
                raise ValueError("管理员密码哈希格式无效，请使用密码配置脚本重新生成") from error

    def login(self, username, password, address):
        if self.database is None and (not self.username or not self.password_hash):
            raise HTTPException(503, "尚未配置管理员账号，请先按照启动说明设置用户名和密码哈希")
        with self.lock:
            now = time.monotonic()
            self.failures = {key: value for key, value in self.failures.items() if value[1] > now}
            count, deadline = self.failures.get(address, (0, now + 300))
            if count >= 5:
                raise HTTPException(429, "登录失败次数过多，请五分钟后重试")
            if self.database:
                with self.database.connect() as connection:
                    row = connection.execute(
                        "SELECT id,username,password_hash,role,enabled FROM users WHERE username=?",
                        (username,),
                    ).fetchone()
                user = dict(row) if row else None
            else:
                user = {
                    "id": None,
                    "username": self.username,
                    "password_hash": self.password_hash,
                    "role": "superadmin",
                    "enabled": 1,
                }
            # 不存在的账号也执行同成本哈希，统一失败提示，减少账号枚举。
            stored_hash = user["password_hash"] if user else f"scrypt${'00' * 16}${'00' * 64}"
            _, salt, expected = stored_hash.split("$")
            digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
            valid_password = secrets.compare_digest(digest, expected)
            if (
                not valid_password
                or not user
                or not user["enabled"]
                or not secrets.compare_digest(username.encode(), user["username"].encode())
            ):
                self.failures[address] = (count + 1, deadline)
                raise HTTPException(401, "账号或密码不正确")
            self.failures.pop(address, None)
            self.sessions = {key: expiry for key, expiry in self.sessions.items() if expiry > now}
            self.identities = {key: value for key, value in self.identities.items() if key in self.sessions}
            token = secrets.token_urlsafe(32)
            self.sessions[token] = now + SESSION_SECONDS
            self.identities[token] = {"id": user["id"], "username": user["username"], "role": user["role"]}
            return token

    def session(self, token):
        with self.lock:
            if not token or self.sessions.get(token, 0) <= time.monotonic():
                self.sessions.pop(token, None)
                self.identities.pop(token, None)
                return None
            identity = self.identities.get(token)
            if self.database and identity:
                with self.database.connect() as connection:
                    row = connection.execute(
                        "SELECT id,username,role,enabled FROM users WHERE id=?", (identity["id"],)
                    ).fetchone()
                if not row or not row["enabled"]:
                    self.sessions.pop(token, None)
                    self.identities.pop(token, None)
                    return None
                return {"id": row["id"], "username": row["username"], "role": row["role"]}
            return identity

    def logout(self, token):
        with self.lock:
            self.sessions.pop(token, None)
            self.identities.pop(token, None)
