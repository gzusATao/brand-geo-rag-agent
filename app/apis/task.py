from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.apis.base import RequestModel
from app.apis.project import ProjectResponse


class CsvImportRequest(RequestModel):
    content: str = Field(
        min_length=1, max_length=500_000, description="包含问题、回答、模型和来源列的CSV文本"
    )


class MockBatchRequest(RequestModel):
    question_ids: list[int] = Field(min_length=1, max_length=100, description="本次模拟监测的启用问句标识")

    @field_validator("question_ids")
    @classmethod
    def unique_ids(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("问句标识不能重复")
        return value


class BatchResponse(BaseModel):
    id: int = Field(description="监测批次唯一标识")
    project_id: int = Field(description="监测批次所属项目标识")
    source: Literal["mock", "historical", "real", "mixed"] = Field(
        description="批次数据来源，模拟、历史、真实或混合"
    )
    status: Literal["pending", "running", "completed", "failed"] = Field(description="监测批次执行状态")
    total: int = Field(description="批次计划处理的回答数量")
    completed: int = Field(description="批次已保存的回答数量")
    error: str | None = Field(description="批次失败原因，无错误时为空")
    created_at: str = Field(description="批次创建时间，格式为年月日时分秒")
    updated_at: str = Field(description="批次最后修改时间，格式为年月日时分秒")


class BrandEvidence(BaseModel):
    brand: str = Field(description="识别结果对应的品牌规范名称")
    mentioned: bool = Field(description="回答中是否明确提及该品牌或其别名")
    recommended: bool = Field(description="规则是否识别出明确的正向推荐表达，属于待核验基线结果")
    rank: int | None = Field(description="显式编号列表中的品牌推荐位置，无明确编号时为空")
    evidence: list[str] = Field(description="用于核对品牌提及及推荐的回答原文片段")


class AnswerResponse(BaseModel):
    id: int = Field(description="原始回答唯一标识")
    batch_id: int = Field(description="回答所属监测批次标识")
    project_id: int = Field(description="回答所属品牌项目标识")
    question: str = Field(description="采集或导入时的问句快照")
    answer: str = Field(description="未经覆盖修改的模型回答原文")
    model: str = Field(description="回答来源模型的标识")
    source: Literal["mock", "historical", "real"] = Field(
        description="回答的数据来源，由导入者声明或模拟器确定"
    )
    collected_date: str | None = Field(description="回答采集日期，格式为年月日，未提供时为空")
    extraction: list[BrandEvidence] = Field(description="基于品牌词典和规则得到的结构化证据")
    extractor_version: str = Field(description="用于复现结构化提取的算法版本")
    created_at: str = Field(description="回答入库时间，格式为年月日时分秒")
    updated_at: str = Field(description="记录最后修改时间，格式为年月日时分秒")


class BrandMetric(BaseModel):
    brand: str = Field(description="指标对应的品牌规范名称")
    mention_count: int = Field(description="有效回答中明确提及该品牌的数量")
    recommendation_count: int = Field(description="规则识别为明确正向推荐该品牌的回答数量")
    mention_rate: float = Field(description="品牌提及回答数除以当前筛选范围内有效回答数")
    recommendation_rate: float = Field(description="品牌推荐回答数除以当前筛选范围内有效回答数")
    rank_distribution: dict[str, int] = Field(description="可观察的显式编号推荐位置及对应回答数量")


class MetricsResponse(BaseModel):
    sample_count: int = Field(description="当前来源和批次筛选下参与统计的回答数量")
    source_counts: dict[str, int] = Field(description="参与统计的真实、历史和模拟回答数量")
    brands: list[BrandMetric] = Field(description="目标品牌和竞品的确定性统计结果")
    warning: str = Field(description="规则提取和模拟数据的解释边界")


class AnalysisResponse(BatchResponse):
    brand: str = Field(description="分析批次所属项目的目标品牌")
    project_name: str = Field(description="分析批次所属项目名称")
    question: str = Field(description="批次已保存问句的摘要，尚无回答时说明等待执行")


class AnalysisPage(BaseModel):
    items: list[AnalysisResponse] = Field(description="当前页的分析批次记录，包含单问句和导入批次")
    total: int = Field(description="符合筛选条件的分析批次总数")


class AnalysisDetail(BaseModel):
    batch: BatchResponse = Field(description="当前分析批次的执行状态和来源信息")
    project: ProjectResponse = Field(description="分析所属项目的品牌与竞品词典")
    metrics: MetricsResponse = Field(description="仅根据本批次回答计算的品牌指标")
    answers: list[AnswerResponse] = Field(description="当前分页的回答原文与品牌提取证据")
    total_answers: int = Field(description="该批次已保存的回答总数")
