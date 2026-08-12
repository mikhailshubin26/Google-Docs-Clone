"""
Доменные исключения

Классы описывают только то, что пошло не так с точки зрения бизнес-правил

ВАЖНО: Домен не должен зависеть от того, как именно он используется снаружи
"""

# Базовый класс для всех доменных исключений
class DomainError(Exception):
    pass

# Сущность не найдена
class EntityNotFoundError(DomainError):
    def __init__(self, entity_name: str, entity_id: object):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f'{entity_name} with id={entity_id} not found')

# Сущность уже существует
class EntityAlreadyExistsError(DomainError):
    def __init__(self, entity_name: str, field: str, value: object):
        self.entity_name = entity_name
        self.field = field
        self.value = value
        super().__init__(f"{entity_name} with {field}={value} already exists")

# ---------------------------------------------------------------------------
# User / Auth
# ---------------------------------------------------------------------------

# Пользователь не найден
class UserNotFoundError(EntityNotFoundError):
    def __init__(self, user_id: object):
        super().__init__(entity_name="User", entity_id=user_id)

# Пользователь уже существует
class UserAlreadyExistsError(EntityAlreadyExistsError):
    def __init__(self, email: str):
        super().__init__(entity_name="User", field="email", value=email)

# Неверные данные пользователя. Не наследуется от EntityNotFoundError для защиты от "атаки перечислением"
class InvalidCredentialsError(DomainError):
    def __init__(self):
        super().__init__("Invalid email or password")

# JWT невалиден, истёк или не прошёл проверку подписи
class InvalidTokenError(DomainError):
    def __init__(self, reason: str = "Token is invalid or expired"):
        super().__init__(reason)

# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

class DocumentNotFoundError(EntityNotFoundError):
    def __init__(self, document_id: object):
        super().__init__(entity_name="Document", entity_id=document_id)

# ---------------------------------------------------------------------------
# Permission
# ---------------------------------------------------------------------------

# У пользователя нет прав на запрошенное действие
class PermissionDeniedError(DomainError):
    def __init__(self, user_id: object, document_id: object, required_role: str):
        self.user_id = user_id
        self.document_id = document_id
        self.required_role = required_role
        super().__init__(
            f"User {user_id!r} lacks '{required_role}' permission "
            f"on document {document_id!r}"
        )

# ---------------------------------------------------------------------------
# OT / Collaboration
# ---------------------------------------------------------------------------

# Операция клиента ссылается на revision, которого нет в логе
class OperationConflictError(DomainError):
    def __init__(self, base_revision: int, current_revision: int):
        self.base_revision = base_revision
        self.current_revision = current_revision
        super().__init__(
            f"Cannot apply operation based on revision={base_revision}, "
            f"current revision is {current_revision}"
        )

# Операция некорректна
class InvalidOperationError(DomainError):
    def __init__(self, reason: str):
        super().__init__(f"Invalid operation: {reason}")