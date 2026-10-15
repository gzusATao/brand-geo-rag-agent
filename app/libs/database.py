"""演示库连接。结构初始化由用户运行独立命令，不在启动时自动建表。"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor


class Database:
    def __init__(self, path=None):
        self.path = path
        self.engine = "sqlite" if path else os.getenv("GEO_DB_ENGINE", "mysql")
        if self.engine not in {"mysql", "sqlite"}:
            raise ValueError("数据库类型只能为mysql或sqlite")
        if self.engine == "sqlite" and not path:
            self.path = os.getenv("GEO_DATABASE_PATH", "data/geo.db")
        self.integrity_errors = (sqlite3.IntegrityError, pymysql.IntegrityError)

    def mysql_connect(self, select_database=True):
        user = os.getenv("GEO_MYSQL_USER", "")
        if not user:
            raise RuntimeError("尚未配置MySQL账号，请先执行 python -m scripts.configure_mysql")
        try:
            return pymysql.connect(
                host=os.getenv("GEO_MYSQL_HOST", "127.0.0.1"),
                port=int(os.getenv("GEO_MYSQL_PORT", "3306")),
                user=user,
                password=os.getenv("GEO_MYSQL_PASSWORD", ""),
                database=os.getenv("GEO_MYSQL_DATABASE", "brand_geo_rag_agent") if select_database else None,
                charset="utf8mb4",
                cursorclass=DictCursor,
                autocommit=False,
                connect_timeout=5,
                read_timeout=15,
                write_timeout=15,
                # 同秒重复停用/启用也应按匹配行数返回，不能误判问句不存在。
                client_flag=pymysql.constants.CLIENT.FOUND_ROWS,
            )
        except (pymysql.MySQLError, ValueError):
            # 不回显连接参数和驱动异常，防止账号或连接信息进入日志。
            raise RuntimeError("MySQL连接失败，请检查服务状态、连接配置及数据库权限") from None

    @contextmanager
    def connect(self):
        if self.engine == "mysql":
            connection = self.mysql_connect()
            try:
                yield MySQLConnection(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()
            return
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def check_schema(self):
        if self.engine == "sqlite" and not Path(self.path).is_file():
            raise RuntimeError("演示数据库尚未初始化，请先执行 python -m scripts.init_db")
        with self.connect() as connection:
            if self.engine == "mysql":
                tables = {
                    row["table_name"]
                    for row in connection.execute(
                        "SELECT TABLE_NAME AS table_name FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()"
                    )
                }
            else:
                tables = {
                    row["name"]
                    for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
                }
        if (
            not {
                "projects",
                "questions",
                "batches",
                "answers",
                "documents",
                "chunks",
                "optimizations",
                "reviews",
                "users",
            }
            <= tables
        ):
            raise RuntimeError("演示数据库表结构不完整，请先执行 python -m scripts.init_db")


class MySQLConnection:
    """保留现有服务的execute接口，只在驱动边界适配参数和日期，不另设业务查询层。"""

    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql, parameters=()):
        cursor = self.connection.cursor()
        cursor.execute(mysql_parameters(sql), parameters)
        return MySQLResult(cursor)

    def executemany(self, sql, parameters):
        cursor = self.connection.cursor()
        cursor.executemany(mysql_parameters(sql), parameters)
        return MySQLResult(cursor)


class MySQLResult:
    def __init__(self, cursor):
        self.lastrowid = cursor.lastrowid
        self.rowcount = cursor.rowcount
        self.rows = [format_row(row) for row in cursor.fetchall()] if cursor.description else []
        self.position = 0
        cursor.close()

    def fetchone(self):
        if self.position >= len(self.rows):
            return None
        row = self.rows[self.position]
        self.position += 1
        return row

    def fetchall(self):
        rows = self.rows[self.position :]
        self.position = len(self.rows)
        return rows

    def __iter__(self):
        return iter(self.fetchall())


def mysql_parameters(sql):
    # 现有业务SQL统一使用问号参数，字符串中的问号和百分号不是占位符。
    result = []
    quote = None
    escaped = False
    for character in sql:
        if character == "%":
            result.append("%%")
        elif character == "?" and quote is None:
            result.append("%s")
        else:
            result.append(character)
        if escaped:
            escaped = False
        elif character == "\\" and quote:
            escaped = True
        elif character in {"'", '"', "`"}:
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
    return "".join(result)


def format_row(row):
    return {
        key: value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, datetime)
        else value.strftime("%Y-%m-%d")
        if isinstance(value, date)
        else value
        for key, value in row.items()
    }
