from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from enum import IntEnum

# Чем более "сильный" пользователь, тем больше его числовое значение
class Role(IntEnum):
    VIEWER = 1
    EDITOR = 2
    OWNER = 3

    def satisfiles(self, required: "Role") -> bool:
        return self >= required

# Permission — Описывает права, которые имеет пользователь на работу с документом
@dataclass
class Permission:
    document_id: UUID
    user_id: UUID
    role: Role
    granted_at: datetime