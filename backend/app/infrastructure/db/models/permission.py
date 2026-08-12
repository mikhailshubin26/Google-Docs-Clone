import uuid

from app.infrastructure.db.session import Base

from datetime import datetime

from sqlalchemy import UniqueConstraint, ForeignKey, SmallInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

# ORM-модель разрешений пользователя на документ
class PermissionModel(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        # Один пользователь — одна роль на документ
        UniqueConstraint("document_id", "user_id", name="uq_permission_document_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)