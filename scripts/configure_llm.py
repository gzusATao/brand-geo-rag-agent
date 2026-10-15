"""通过本地隐藏输入配置百炼；不在命令行、网页或日志中回显密钥。"""

from getpass import getpass
from pathlib import Path

from dotenv import set_key

from app.libs.qwen_client import valid_qwen_endpoint


def main():
    base = (
        input("百炼接口地址 [https://dashscope.aliyuncs.com/compatible-mode/v1]：").strip()
        or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    model = input("模型名称 [qwen-plus]：").strip() or "qwen-plus"
    key = getpass("百炼 API Key（隐藏输入）：").strip()
    if not key or not key.isascii() or not valid_qwen_endpoint(base):
        raise SystemExit("请提供百炼 HTTPS 接口及非空密钥，配置未保存")
    path = Path(__file__).resolve().parents[1] / ".env"
    for name, value in {
        "GEO_QWEN_API_KEY": key,
        "GEO_QWEN_BASE_URL": base.rstrip("/"),
        "GEO_QWEN_MODEL": model,
    }.items():
        set_key(path, name, value)
    print("百炼配置已保存到本项目忽略提交的.env；请重启服务。尚未发起付费调用或验证连通性。")


if __name__ == "__main__":
    main()
