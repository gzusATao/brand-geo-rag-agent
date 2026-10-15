from fastapi import APIRouter, Request

from app.apis.knowledge_base import (
    DocumentContentResponse,
    DocumentCreate,
    DocumentResponse,
    RetrievalHit,
    RetrievalRequest,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.get(
    "/projects/{project_id}/knowledge/documents/{document_id}",
    response_model=DocumentContentResponse,
    tags=["知识库"],
)
def document_content(project_id: int, document_id: int, request: Request):
    return KnowledgeService(request.app.state.database).document(project_id, document_id)


@router.post(
    "/projects/{project_id}/knowledge/documents",
    response_model=DocumentResponse,
    status_code=201,
    tags=["知识库"],
)
def add_document(project_id: int, payload: DocumentCreate, request: Request):
    return KnowledgeService(request.app.state.database).add_document(project_id, payload)


@router.get(
    "/projects/{project_id}/knowledge/documents", response_model=list[DocumentResponse], tags=["知识库"]
)
def list_documents(project_id: int, request: Request):
    return KnowledgeService(request.app.state.database).documents(project_id)


@router.post("/projects/{project_id}/knowledge/retrieve", response_model=list[RetrievalHit], tags=["知识库"])
def retrieve(project_id: int, payload: RetrievalRequest, request: Request):
    return KnowledgeService(request.app.state.database).retrieve(project_id, payload.query, payload.top_k)
