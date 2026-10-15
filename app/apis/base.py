"""请求与响应契约。首版只提供明确标识的数据来源和规则基线。"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("*", mode="after")
    @classmethod
    def reject_blank_strings(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError("文本内容不能为空")
        return value


class HealthResponse(BaseModel):
    status: str = Field(description="当前服务运行状态")
    version: str = Field(description="当前毕业设计原型版本")
