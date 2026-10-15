"""管理员初始化属于业务数据操作，独立于建表SQL。"""

from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv

from app.auth.auth import hash_password
from app.libs.database import Database
from app.utils.date_utils import timestamp


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    password = getpass("请输入admin的登录密码（仅本地演示可使用简单密码）：")
    if not password or len(password) > 256:
        raise SystemExit("密码不能为空且不能超过256位")
    if password != getpass("请再次输入登录密码："):
        raise SystemExit("两次输入的密码不一致")
    create_admin(Database(), password)
    print("超级管理员admin已创建，密码以带盐哈希保存；简单密码仅限本机演示")


def create_admin(database, password):
    database.check_schema()
    now = timestamp()
    with database.connect() as connection:
        if connection.execute("SELECT id FROM users WHERE username=?", ("admin",)).fetchone():
            raise RuntimeError("admin账号已存在，未覆盖原密码或权限")
        connection.execute(
            "INSERT INTO users(username,password_hash,role,enabled,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            ("admin", hash_password(password), "superadmin", 1, now, now),
        )


if __name__ == "__main__":
    main()
