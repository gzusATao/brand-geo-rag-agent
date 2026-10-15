from typing import Literal

from pydantic import BaseModel, Field

from app.apis.base import RequestModel


class AgentChatRequest(RequestModel):
    message: str = Field(min_length=1, max_length=2000, description="用户本轮品牌研究问题或优化要求")
    session_id: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{32}$", description="当前项目的内存会话标识，首次对话不传"
    )


class AgentModelStatus(BaseModel):
    configured: bool = Field(description="是否已配置百炼密钥和有效接口地址，不代表已验证模型连通性")
    model: str = Field(description="当前配置的通义千问模型名称")
    provider: str = Field(description="模型服务提供方")
    notice: str = Field(description="配置状态和数据传输范围说明")


class AgentTrace(BaseModel):
    agent: Literal["supervisor", "rag", "tool", "summary"] = Field(
        description="执行角色，分别为主管、检索、工具和摘要智能体"
    )
    status: Literal["pending", "running", "completed", "skipped", "failed"] = Field(
        description="该智能体当前的公开执行状态"
    )
    summary: str = Field(description="便于用户核对的执行摘要，不包含模型内部思维链")


class AgentCitation(BaseModel):
    chunk_id: int = Field(description="本项目中被引用的知识片段标识")
    title: str = Field(description="被引用企业资料的标题")
    source: str = Field(description="企业资料录入时注明的来源，不代表已联网核验")
    text: str = Field(description="用于核对模型回答的知识原文片段")


class AgentChatRun(BaseModel):
    id: str = Field(description="本轮多智能体执行任务标识")
    session_id: str = Field(description="本轮任务所属的项目内存会话标识")
    project_id: int = Field(description="会话所属的品牌项目标识")
    status: Literal["pending", "running", "completed", "failed"] = Field(
        description="本轮多智能体任务执行状态"
    )
    answer: str | None = Field(description="完成后返回的模型汇总答复，未完成时为空")
    error: str | None = Field(description="失败时的中文原因，其他状态为空")
    trace: list[AgentTrace] = Field(description="主管及各专业智能体的公开执行轨迹")
    citations: list[AgentCitation] = Field(description="答复引用并通过片段标识校验的本项目知识证据")
    created_at: str = Field(description="任务创建时间，格式为年月日时分秒")
    updated_at: str = Field(description="任务最近更新时间，格式为年月日时分秒")


class AgentMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(description="会话消息角色，用户或智能体助理")
    content: str = Field(description="已完成轮次的用户消息或模型回复")


class AgentSession(BaseModel):
    session_id: str = Field(description="项目内存会话标识")
    project_id: int = Field(description="该会话所属品牌项目标识")
    messages: list[AgentMessage] = Field(description="最近已完成轮次的对话，服务重启后不保留")


class SupervisorPlan(RequestModel):
    intent: Literal["analysis", "knowledge", "article", "chat"] = Field(
        description="主管识别的监测分析、知识问答、文章草稿或一般对话意图"
    )
    query: str = Field(min_length=1, max_length=500, description="根据本轮消息与历史补全的知识检索问句")
    agents: list[Literal["rag", "tool"]] = Field(
        max_length=2, description="主管选择执行的白名单专业智能体，摘要汇总由系统最后执行"
    )


class GroundedAnswer(RequestModel):
    answer: str = Field(min_length=1, max_length=8000, description="智能体基于现有证据生成的中文答复")
    citation_ids: list[int] = Field(
        max_length=5, description="答复实际使用的本项目知识片段标识，证据不足时为空"
    )
