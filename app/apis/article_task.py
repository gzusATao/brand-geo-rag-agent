from typing import Literal

from pydantic import BaseModel, Field

from app.apis.base import RequestModel
from app.apis.knowledge_base import RetrievalHit, RetrievalRequest


class OptimizationRequest(RetrievalRequest):
    pass


class TraceStep(BaseModel):
    tool: str = Field(description="本次固定工作流调用的工具名称")
    status: str = Field(description="工具执行状态")
    summary: str = Field(description="工具输入输出的简短摘要")


class OptimizationResponse(BaseModel):
    id: int = Field(description="辅助优化运行唯一标识")
    project_id: int = Field(description="运行所属品牌项目标识")
    query: str = Field(description="本次内容优化的目标问句")
    mode: str = Field(description="运行方式，首版为固定工具工作流演示，不是自主智能体")
    diagnosis: str = Field(description="基于非模拟监测样本形成的基线诊断或证据不足提示")
    suggestions: list[str] = Field(description="供人工核验的内容整理建议")
    citations: list[RetrievalHit] = Field(description="草稿实际使用的品牌资料证据")
    trace: list[TraceStep] = Field(description="固定工具调用流程及执行摘要")
    draft: str = Field(description="基于检索片段组装的Markdown草稿，不是模型生成结果")
    review_status: Literal["pending", "approved", "rejected"] = Field(description="当前草稿审核状态")
    review_note: str | None = Field(description="人工审核意见，未审核时为空")
    created_at: str = Field(description="运行创建时间，格式为年月日时分秒")
    updated_at: str = Field(description="运行最后修改时间，格式为年月日时分秒")


class ReviewRequest(RequestModel):
    status: Literal["approved", "rejected"] = Field(description="人工审核决定，通过或驳回")
    note: str = Field(min_length=1, max_length=1000, description="人工审核的事实核对意见")
    draft: str | None = Field(
        default=None, min_length=1, max_length=100_000, description="人工编辑后的草稿，未填写时保留原文"
    )
