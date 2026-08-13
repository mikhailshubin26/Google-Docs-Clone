from typing import Protocol
from uuid import UUID

from app.domain.entities.permission import Role, Permission


# Абстрактный контракт хранилища прав доступа пользователей к документам
class PermissionRepository(Protocol):
    # возвращает роль пользователя в документе. либо None, если прав нет вообще
    async def get_role(self, document_id: UUID, user_id: UUID) -> Role | None:
        ...

    # Выдоёт/заменяет роль пользователя в документе
    async def grant(self, permission: Permission) -> None:
        ...

    # Отзывает права пользователя на документ
    async def revoke(self, document_id: UUID, user_id: UUID) -> None:
        ...

    # возвращает всех пользователей с их правами на документ
    async def list_for_document(self, document_id: UUID) -> list[Permission]:
        ...