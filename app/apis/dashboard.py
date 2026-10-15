from pydantic import BaseModel, Field

from app.apis.task import AnswerResponse, MetricsResponse


class TrendPoint(BaseModel):
    date: str = Field(description="采样日期，优先采集日期，缺失时使用入库日期，格式为年月日")
    sample_count: int = Field(description="该日期筛选范围内的回答数量")
    mention_rate: float = Field(description="该日期目标品牌提及回答数占有效样本数的比例")
    recommendation_rate: float = Field(description="该日期目标品牌规则推荐回答数占有效样本数的比例")


class QuestionSummary(BaseModel):
    question: str = Field(description="筛选范围内已保存的采集问句原文")
    sample_count: int = Field(description="该问句在筛选范围内已保存的回答数量")


class ModelSummary(BaseModel):
    model: str = Field(description="回答中记录的模型名称，导入时由录入者声明")
    sample_count: int = Field(description="筛选范围内该模型标识的回答数量")


class DashboardResponse(BaseModel):
    metrics: MetricsResponse = Field(description="与时间、来源、问句、模型和批次筛选一致的品牌指标")
    trend: list[TrendPoint] = Field(description="实际有样本日期的目标品牌趋势，不为无数据日期虚构指标")
    questions: list[QuestionSummary] = Field(
        description="当前时间来源范围内可切换的问句及数量，不受当前问句与模型筛选影响"
    )
    models: list[ModelSummary] = Field(
        description="当前时间来源范围内可切换的模型标识及数量，不代表平台已经直连"
    )
    rank_counts: dict[str, int] = Field(
        description="目标品牌推荐位置的互斥样本数量，区分第一位、第二至第三位、其他显式编号和无明确编号"
    )
    answers: list[AnswerResponse] = Field(description="筛选范围内当前分页的原始回答及证据")
    total: int = Field(description="筛选范围内已保存回答总数")
    date_basis: str = Field(description="时间筛选和趋势日期的统一计算口径")
