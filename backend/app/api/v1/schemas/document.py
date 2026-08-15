# pydantic-схемы запросов/ответов для эндпоинтов документов
from datetime import datetime

from pydantic import BaseModel, Field
from uuid import UUID

from app.domain.entities.document import Document


class CreateDocumentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)

class RenameDocumentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)

class DocumentResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    revision: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, document: Document) -> "DocumentResponse":
        return cls(
            id=document.id,
            owner_id=document.owner_id,
            title=document.title,
            revision=document.revision,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

class DocumentContentResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    content: str
    revision: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, document: Document) -> "DocumentContentResponse":
        return cls(
            id=document.id,
            owner_id=document.owner_id,
            title=document.title,
            content=document.content_snapshot,
            revision=document.revision,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    limit: int
    offset: int