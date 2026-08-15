from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domain.entities.permission import Role, Permission
from app.infrastructure.db.models.permission import PermissionModel
from app.mappers.permission import permission_model_to_entity


# Абстрактный контракт хранилища прав доступа пользователей к документам
class SqlAlchemyPermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # возвращает роль пользователя в документе. либо None, если прав нет вообще
    async def get_role(self, document_id: UUID, user_id: UUID) -> Role | None:
        stmt = select(PermissionModel.role).where(
            PermissionModel.document_id == document_id,
            PermissionModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        role_value = result.scalar_one_or_none()
        return Role(role_value) if role_value else None

    # Выдоёт/заменяет роль пользователя в документе
    async def grant(self, permission: Permission) -> None:
        stmt = pg_insert(PermissionModel).values(
            document_id=permission.document_id,
            user_id=permission.user_id,
            role=int(permission.role),
            granted=permission.granted_at,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_permission_document_user",
            set={"role": stmt.excluded.role, "granted_at": stmt.excluded.granted_at},
        )
        await self._session.execute(stmt)
        await self._session.flush()

    # Отзывает права пользователя на документ
    async def revoke(self, document_id: UUID, user_id: UUID) -> None:
        stmt = select(PermissionModel).where(
            PermissionModel.document_id == document_id,
            PermissionModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    # возвращает всех пользователей с их правами на документ
    async def list_for_document(self, document_id: UUID) -> list[Permission]:
        stmt = select(PermissionModel).where(
            PermissionModel.document_id == document_id,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [permission_model_to_entity(m) for m in models]