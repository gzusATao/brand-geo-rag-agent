"""本地交互保存连接配置，不把数据库密码放在命令行参数中。"""

from getpass import getpass
from pathlib import Path

import pymysql
from dotenv import set_key


def main():
    host = input("MySQL地址 [127.0.0.1]：").strip() or "127.0.0.1"
    port = input("MySQL端口 [3306]：").strip() or "3306"
    username = input("MySQL连接账号：").strip()
    password = getpass("MySQL连接密码：")
    if not username or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise SystemExit("账号不能为空，端口必须在1至65535之间")
    try:
        connection = pymysql.connect(
            host=host, port=int(port), user=username, password=password, connect_timeout=5
        )
        connection.close()
    except pymysql.MySQLError:
        raise SystemExit("MySQL连接失败，未保存配置；请检查服务、账号密码和权限") from None
    path = Path(__file__).resolve().parents[1] / ".env"
    for key, value in {
        "GEO_DB_ENGINE": "mysql",
        "GEO_MYSQL_HOST": host,
        "GEO_MYSQL_PORT": port,
        "GEO_MYSQL_USER": username,
        "GEO_MYSQL_PASSWORD": password,
        "GEO_MYSQL_DATABASE": "brand_geo_rag_agent",
        "GEO_SESSION_SECURE": "0",
    }.items():
        set_key(path, key, value)
    print("连接配置已保存到本项目忽略提交的.env；未创建数据库或写入业务数据")


if __name__ == "__main__":
    main()
