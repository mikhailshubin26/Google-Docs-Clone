from uuid import UUID
from datetime import datetime, timezone

from app.domain.entities.permission import Role, Permission
from app.domain.exceptions import PermissionDeniedError
from app.domain.repositories.document import DocumentRepository
from app.domain.repositories.permission import PermissionRepository

# Бизнес-логика проверки и управления правами доступа к документам
class PermissionService:
    def __init__(self, document_repo: DocumentRepository, permission_repo: PermissionRepository) -> None:
        self._document_repo = document_repo
        self._permission_repo = permission_repo

    # Возвращает фактическую роль пользователя в документе
    async def get_effective_role(self, document_id: UUID, user_id: UUID) -> Role | None:
        owner_id = await self._document_repo.get_owner_id(document_id)
        if owner_id == user_id:
            return Role.OWNER
        return await self._permission_repo.get_role(document_id, user_id)

    # Проверяет, что у пользователя достаточно прав
    async def check_permission(self, document_id: UUID, user_id: UUID, required_role: Role) -> None:
        role = await self.get_effective_role(document_id, user_id)
        if role is None or not role.satisfies(required_role):
            raise PermissionDeniedError(
                user_id=user_id,
                document_id=document_id,
                required_role=required_role.name,
            )

    # Выдаёт права пользователю на документ
    async def grant_role(self, document_id: UUID, target_user_id: UUID, role: Role) -> None:
        permission = Permission(
            document_id=document_id,
            user_id=target_user_id,
            role=role,
            granted_at=datetime.now(timezone.utc),
        )
        await self._permission_repo.grant(permission)

    # Отзывает права пользователя на документ
    async def revoke_role(self, document_id: UUID, target_user_id: UUID) -> None:
        await self._permission_repo.revoke(document_id, target_user_id)