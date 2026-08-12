from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

"""
Document — Описывает метаданные документа, но не его содержание, так как последнее
формируется из снапшота, хранящегося в Postgres + лога операций поверх него
"""

@dataclass
class Document:
    id: UUID
    owner_id: UUID
    title: str
    content_snapshot: str
    revision: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    # метод переименования документа
    def rename(self, new_title: str) -> None:
        if not new_title.strip():
            raise ValueError("Document title cannot be empty")
        self.title = new_title
        self.updated_at = datetime.utcnow()

    # применить изменения к документу
    def apply_snapshot(self, content: str, revision: int) -> None:
        if revision < self.revision:
            raise ValueError(
                f"Cannot apply stale snapshot: current revision={self.revision}, got revision={revision}"
            )
        self.content_snapshot = content
        self.revision = revision
        self.updated_at = datetime.utcnow()

    # метод мягкого удаления
    def mark_deleted(self) -> None:
        self.deleted_at = datetime.utcnow()

    def is_deleted(self) -> bool:
        return self.deleted_at is not None