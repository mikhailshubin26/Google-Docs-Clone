from typing import Protocol
from uuid import UUID

from backend.app.domain.entities.document import Document

# Абстрактный контракт хранилища документов

class DocumentRepository(Protocol):
    async def get_by_id(self, document_id: UUID) -> Document | None:
        ...

    async def list_by_owner(self, owner_id: UUID, limit: int, offset: int) -> list[Document]:
        ...

    async def create(self, document: Document) -> None:
        ...

    # update используется и для rename(), и для apply_snapshot(), и для mark_deleted()
    async def update(self, document: Document) -> None:
        ...

    # узкоспециальный метод для проверки прав пользователя на документ
    async def get_owner_id(self, document_id: UUID) -> UUID | None:
        ...