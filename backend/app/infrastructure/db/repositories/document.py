from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document import Document
from app.infrastructure.db.models import DocumentModel
from app.mappers.document import document_model_to_entity, document_entity_to_model, apply_document_entity_to_model
from uuid import UUID



# Реализация DocumentRepository (интерфейс из app/domain/repositories/document.py)
class SqlAlchemyDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, document_id: UUID) -> Document | None:
        model = await self._session.get(DocumentModel, document_id)
        if model is None:
            return None
        return document_model_to_entity(model)

    async def list_by_owner(self, owner_id: UUID, limit: int, offset: int) -> list[Document]:
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.owner_id == owner_id)
            .where(DocumentModel.deleted_at.is_(None))
            .order_by(DocumentModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [document_model_to_entity(m) for m in models]

    async def create(self, document: Document) -> None:
        model = document_entity_to_model(document)
        self._session.add(model)
        await self._session.flush()

    # update используется и для rename(), и для apply_snapshot(), и для mark_deleted()
    async def update(self, document: Document) -> None:
        model = await self._session.get(DocumentModel, document.id)
        if model is None:
            raise ValueError(f"Cannot update: document {document.id} does not exist")
        apply_document_entity_to_model(document, model)
        await self._session.flush()

    # узкоспециальный метод для проверки прав пользователя на документ
    async def get_owner_id(self, document_id: UUID) -> UUID | None:
        stmt = select(DocumentModel.owner_id).where(DocumentModel.id == document_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()