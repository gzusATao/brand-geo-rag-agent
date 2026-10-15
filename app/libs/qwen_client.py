import asyncio
import json
import os
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException


def valid_qwen_endpoint(base_url):
    try:
        endpoint = urlsplit(base_url)
    except ValueError:
        return False
    host = endpoint.hostname or ""
    return bool(
        endpoint.scheme == "https"
        and (
            host in {"dashscope.aliyuncs.com", "dashscope-intl.aliyuncs.com", "dashscope-us.aliyuncs.com"}
            or host.endswith(".maas.aliyuncs.com")
        )
        and not endpoint.username
        and not endpoint.password
        and not endpoint.query
        and not endpoint.fragment
    )


class QwenClient:
    def __init__(self):
        self.key = os.getenv("GEO_QWEN_API_KEY", "").strip()
        self.base_url = os.getenv(
            "GEO_QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ).rstrip("/")
        self.model = os.getenv("GEO_QWEN_MODEL", "qwen-plus").strip()

    def configured(self):
        # 密钥只允许发给百炼 HTTPS 域名；不跟随重定向，避免错误地址泄漏密钥。
        return bool(self.key and self.key.isascii() and self.model and valid_qwen_endpoint(self.base_url))

    async def complete(self, system, context, schema):
        if not self.configured():
            raise HTTPException(503, "百炼模型尚未配置，请先运行本地模型配置脚本并重启服务")
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system
                    + "\n只返回符合下列 JSON Schema 的 JSON 对象："
                    + json.dumps(schema.model_json_schema(), ensure_ascii=False),
                },
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "enable_thinking": False,
            "max_tokens": 1800,
            "temperature": 0.3,
        }
        try:
            async with httpx.AsyncClient(timeout=45, follow_redirects=False, trust_env=False) as client:
                response = await asyncio.wait_for(
                    client.post(
                        self.base_url + "/chat/completions",
                        json=payload,
                        headers={"Authorization": "Bearer " + self.key},
                    ),
                    timeout=45,
                )
            if response.status_code in {401, 403}:
                raise HTTPException(502, "百炼鉴权失败，请核对密钥地域、模型权限和接口地址")
            if response.status_code == 429:
                raise HTTPException(502, "百炼请求受限，请检查额度或稍后重试")
            if response.status_code != 200:
                raise HTTPException(502, "百炼调用失败，请检查模型配置和服务状态")
            result = response.json()["choices"][0]
            if result.get("finish_reason") != "stop":
                raise HTTPException(502, "模型输出未完整结束，本轮未保存为成功结果")
            return schema.model_validate_json(result["message"]["content"])
        except (httpx.TimeoutException, asyncio.TimeoutError):
            raise HTTPException(504, "百炼模型响应超时，请稍后重试") from None
        except httpx.HTTPError:
            raise HTTPException(502, "无法连接百炼模型，请检查网络和接口配置") from None
        except (ValueError, KeyError, IndexError, TypeError):
            # 不回显服务商原始响应，避免提示词、密钥或企业资料进入错误信息。
            raise HTTPException(502, "模型未返回有效的结构化结果，本轮未保存为成功结果") from None
