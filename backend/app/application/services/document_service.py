# Бизнес-логика CRUD-операций над документами
import uuid
from uuid import UUID
from datetime import datetime, timezone

from app.domain.exceptions import DocumentNotFoundError
from app.domain.repositories.document import DocumentRepository
from app.application.services.permission_service import PermissionService
from app.domain.entities.document import Document
from app.domain.entities.permission import Role


class DocumentService:
    def __init__(self, document_repo: DocumentRepository, permission_service: PermissionService) -> None:
        self._document_repo=document_repo
        self._permission_service=permission_service

    # Создать новый документ и выдать владельцу роль OWNER
    async def create_document(self, owner_id: UUID, title: str) -> Document:
        now = datetime.now(timezone.utc)
        document = Document(
            id=uuid.uuid4(),
            owner_id=owner_id,
            title=title,
            content_snapshot="",
            revision=0,
            created_at=now,
            updated_at=now,
        )
        await self._document_repo.create(document)
        await self._permission_service.grant_role(document.id, owner_id, Role.OWNER)
        return document

    # Возвращает документ, если у пользователя есть хотя бы роль VIEWER
    async def get_document(self, document_id: UUID, user_id: UUID) -> Document:
        await self._permission_service.check_permission(document_id, user_id, Role.VIEWER)
        document = await self._document_repo.get_by_id(document_id)
        if document is None or document.is_deleted():
            raise DocumentNotFoundError(document_id)
        return document

    # Возвращает список документов пользователя
    async def list_my_documents(self, owner_id: UUID, limit: int = 20, offset: int = 0) -> list[Document]:
        return await self._document_repo.list_by_owner(owner_id, limit, offset)

    # Переименовать документ
    async def rename_document(self, document_id: UUID, user_id: UUID,  new_title: str) -> Document:
        await self._permission_service.check_permission(document_id, user_id, Role.EDITOR)
        document = await self._document_repo.get_by_id(document_id)
        if document is None or document.is_deleted():
            raise DocumentNotFoundError(document_id)
        document.rename(new_title)
        await self._document_repo.update(document)
        return document

    async def delete_document(self, document_id: UUID, user_id: UUID) -> None:
        await self._permission_service.check_permission(document_id, user_id, Role.OWNER)
        document = await self._document_repo.get_by_id(document_id)
        if document is None or document.is_deleted():
            raise DocumentNotFoundError(document_id)
        document.mark_deleted()
        await self._document_repo.update(document)