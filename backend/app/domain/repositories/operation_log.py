from uuid import UUID
from typing import Protocol

from backend.app.domain.ot.operation import Operation

# Абстрактный контракт лога OT-операций

class OperationLogRepository(Protocol):
    async def append(self, document_id: UUID, revision: int, operation: Operation) -> None:
        ...

    async def get_operations_since(self, document_id: UUID, since_revision: int) -> list[Operation]:
        ...

    async def get_latest_revision(self, document_id: UUID) -> int:
        ...

    """
    Удаляет/архивирует записи лога вплоть до указанной ревизии.
    Вызывается после того, как application-слой схлопнул операции в новый снапшот
    """
    async def compact(self, document_id: UUID, up_to_revision: int) -> None:
        ...