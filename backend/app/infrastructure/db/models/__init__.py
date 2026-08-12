# Собирает все ORM-модели в одном месте

from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.models.document import DocumentModel
from app.infrastructure.db.models.permission import PermissionModel

__all__ = ["UserModel", "DocumentModel", "PermissionModel"]