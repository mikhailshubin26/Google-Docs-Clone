from typing import Protocol
from uuid import UUID

from app.domain.entities.user import User

# Абстрактный контракт хранилища пользователей

class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    async def get_by_email(self, email: str) -> User | None:
        ...

    async def create(self, user: User) -> None:
        ...

    async def update(self, user: User) -> None:
        ...

    async def exists_with_email(self, email: str) -> bool:
        ...