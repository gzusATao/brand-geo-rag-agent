from pydantic import BaseModel, Field

from app.apis.base import RequestModel


class DocumentCreate(RequestModel):
    title: str = Field(min_length=1, max_length=200, description="品牌资料标题")
    source: str = Field(min_length=1, max_length=500, description="品牌资料的公开来源或虚构资料说明")
    content: str = Field(min_length=1, max_length=100_000, description="已脱敏的品牌资料正文")


class DocumentResponse(BaseModel):
    id: int = Field(description="品牌资料唯一标识")
    project_id: int = Field(description="资料所属品牌项目标识")
    title: str = Field(description="品牌资料标题")
    source: str = Field(description="资料来源说明")
    chunk_count: int = Field(description="该资料当前建立的文本片段数量")
    created_at: str = Field(description="资料创建时间，格式为年月日时分秒")
    updated_at: str = Field(description="资料最后修改时间，格式为年月日时分秒")


class RetrievalRequest(RequestModel):
    query: str = Field(min_length=1, max_length=500, description="在本项目知识库内检索的查询文本")
    top_k: int = Field(default=3, ge=1, le=10, description="最多返回的相关资料片段数量")


class DocumentContentResponse(DocumentResponse):
    content: str = Field(description="品牌资料原文，内容由录入者提供并需核验")


class RetrievalHit(BaseModel):
    chunk_id: int = Field(description="命中的文本片段标识")
    document_id: int = Field(description="片段所属资料标识")
    title: str = Field(description="片段所属资料标题")
    source: str = Field(description="片段所属资料来源")
    text: str = Field(description="命中的资料原文片段")
    score: float = Field(description="字符二元组余弦相似度，不是语义向量相关分数")
