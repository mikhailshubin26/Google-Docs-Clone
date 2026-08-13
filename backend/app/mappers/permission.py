from app.infrastructure.db.models import PermissionModel
from app.domain.entities.permission import Permission, Role

# Собирает доменную сущность Permission из строки таблицы permissions
def permission_model_to_entity(model: PermissionModel) -> Permission:
    return Permission(
        document_id=model.document_id,
        user_id=model.user_id,
        role=Role(model.role),
        granted_at=model.granted_at,
    )