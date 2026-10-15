from getpass import getpass

from app.auth.auth import hash_password


def main():
    password = getpass("请输入管理员密码（至少12位）：")
    if len(password) < 12 or len(password) > 256:
        raise SystemExit("密码长度必须在12至256位之间")
    if password != getpass("请再次输入密码："):
        raise SystemExit("两次输入的密码不一致")
    print(hash_password(password))


if __name__ == "__main__":
    main()
