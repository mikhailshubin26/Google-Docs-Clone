# In-memory fake реализация репозиториев
from uuid import UUID

from app.domain.entities.document import Document
from app.domain.entities.permission import Permission, Role
from app.domain.entities.user import User


class FakeUserRepository:

    def __init__(self) -> None:
        self._users: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def create(self, user: User) -> None:
        self._users[user.id] = user

    async def update(self, user: User) -> None:
        self._users[user.id] = user

    async def exists_with_email(self, email: str) -> bool:
        return any(user.email == email for user in self._users.values())

class FakeDocumentRepository:
    def __init__(self) -> None:
        self._documents: dict[UUID, Document] = {}

    async def get_by_id(self, document_id: UUID) -> Document:
        return self._documents.get(document_id)

    async def list_by_owner(self, owner_id: UUID, limit: int, offset: int) -> list[Document] | None:
        matched = [d for d in self._documents.values() if d.owner_id == owner_id and not d.is_deleted()]
        matched.sort(key=lambda d: d.updated_at, reverse=True)
        return matched[offset: offset + limit]

    async def create(self, document: Document) -> None:
        self._documents[document.id] = document

    async def update(self, document: Document) -> None:
        self._documents[document.id] = document

    async def get_owner_id(self, document_id: UUID) -> UUID | None:
        document = self._documents.get(document_id)
        return document.owner_id if document else None

class FakePermissionRepository:
    def __init__(self) -> None:
        # (document_id, user_id) : permission
        self._permissions: dict[tuple[UUID, UUID], Permission] = {}

    async def get_role(self, document_id: UUID, user_id: UUID) -> Role | None:
        permission = self._permissions.get((document_id, user_id))
        return permission.role if permission else None

    async def grant(self, permission: Permission) -> None:
        self._permissions[(permission.document_id, permission.user_id)] = permission

    async def revoke(self, document_id: UUID, user_id: UUID) -> None:
        self._permissions.pop((document_id, user_id), None)

    async def list_for_document(self, document_id: UUID) -> list[Permission]:
        return [p for (doc_id, _), p in self._permissions.items() if doc_id == document_id]