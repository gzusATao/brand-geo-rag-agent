from pydantic import Field, model_validator

from app.apis.base import RequestModel


class ProjectCreate(RequestModel):
    name: str = Field(min_length=1, max_length=100, description="品牌监测项目名称")
    brand: str = Field(min_length=1, max_length=100, description="目标品牌的规范名称")
    aliases: list[str] = Field(default_factory=list, max_length=20, description="目标品牌的其他名称")
    competitors: list[str] = Field(default_factory=list, max_length=20, description="需要比较的竞品规范名称")

    @model_validator(mode="after")
    def validate_brand_names(self):
        names = [self.brand, *self.aliases, *self.competitors]
        if any(not name.strip() or len(name) > 100 for name in names):
            raise ValueError("品牌、别名和竞品名称必须为1至100个字符")
        if len({name.strip().casefold() for name in names}) != len(names):
            raise ValueError("目标品牌、别名和竞品名称不能重复")
        self.aliases = [name.strip() for name in self.aliases]
        self.competitors = [name.strip() for name in self.competitors]
        return self


class ProjectResponse(ProjectCreate):
    id: int = Field(description="项目唯一标识")
    created_at: str = Field(description="项目创建时间，格式为年月日时分秒")
    updated_at: str = Field(description="项目最后修改时间，格式为年月日时分秒")


class MonitorProjectCreate(ProjectCreate):
    initial_questions: list[str] = Field(
        default_factory=list,
        max_length=100,
        description="创建项目时同时录入的监测问句，每条需包含文字或数字且不重复",
    )


class QuestionCreate(RequestModel):
    text: str = Field(min_length=1, max_length=500, description="用于采集自然回答的监测问句")


class QuestionResponse(QuestionCreate):
    id: int = Field(description="监测问句唯一标识")
    project_id: int = Field(description="问句所属项目标识")
    enabled: bool = Field(description="问句是否启用监测")
    created_at: str = Field(description="问句创建时间，格式为年月日时分秒")
    updated_at: str = Field(description="问句最后修改时间，格式为年月日时分秒")


class QuestionUpdate(RequestModel):
    enabled: bool = Field(description="是否启用该监测问句")


class ProjectNameUpdate(RequestModel):
    name: str = Field(min_length=1, max_length=100, description="修改后的监测项目名称")


class MonitorProjectResponse(ProjectResponse):
    question_count: int = Field(description="项目当前启用的监测问句数量")
    status: str = Field(description="最新监测批次状态，无批次时为draft")


class MonitorProjectPage(RequestModel):
    items: list[MonitorProjectResponse] = Field(description="当前页的监测项目记录")
    total: int = Field(description="符合筛选条件的项目总数")
