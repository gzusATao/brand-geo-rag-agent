"""显式初始化独立演示库，不连接公司数据库。"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from app.libs.database import Database


def main():
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
    database = Database()
    if database.engine == "mysql":
        # 初始化程序只允许操作指定独立库，避免误用公司连接配置。
        if os.getenv("GEO_MYSQL_DATABASE", "brand_geo_rag_agent") != "brand_geo_rag_agent":
            raise SystemExit("初始化只允许操作独立数据库brand_geo_rag_agent")
        with database.mysql_connect(select_database=False) as connection:
            with connection.cursor() as cursor:
                sql = (root / "sql" / "schema.mysql.sql").read_text(encoding="utf-8")
                for statement in sql.split(";"):
                    if statement.strip():
                        cursor.execute(statement)
        database.check_schema()
        print("独立MySQL库brand_geo_rag_agent的9张表已初始化，未写入业务数据")
        return
    path = Path(os.getenv("GEO_DATABASE_PATH", "data/geo.db")).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    sql = Path(__file__).resolve().parents[1] / "sql" / "schema.sqlite.sql"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(sql.read_text(encoding="utf-8"))
    print(f"独立演示库初始化完成：{path}")


if __name__ == "__main__":
    main()
