from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID
from app.infrastructure.db.models import UserModel
from app.domain.entities.user import User

from app.mappers.user import user_model_to_entity, user_entity_to_model, apply_user_entity_to_model

# Реализация UserRepository (интерфейс из app/domain/repositories/user.py)
class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            return None
        return user_model_to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return user_model_to_entity(model)

    async def create(self, user: User) -> None:
        model = user_entity_to_model(user)
        self._session.add(model)
        await self._session.flush()

    async def update(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"Cannot update: user {user.id} does not exist")
        apply_user_entity_to_model(user, model)
        await self._session.flush()

    async def exists_with_email(self, email: str) -> bool:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        return bool(result.scalar())