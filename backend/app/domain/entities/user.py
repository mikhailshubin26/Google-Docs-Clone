from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

# User — Описывает пользователя так, как его понимает бизнес-логика
@dataclass
class User:
    id: UUID
    display_name: str
    is_guest: bool
    created_at: datetime
    email: str | None = None
    password_hash: str | None = None

    # Проверка на уровне домена: НЕ-ГОСТЬ обязан иметь email и пароль
    def __post_init__(self) -> None:
        if not self.is_guest and (self.email is None and self.password_hash is None):
            raise ValueError("Non-guest user must have both email and password_hash")

    # Проверка: может ли пользователь апгрейднуться с гостя до полноценного пользователя
    def can_be_upgraded_to_registred(self) -> bool:
        return self.is_guest

    # Метод превращения гостя в полноценного пользователя
    def upgrade_to_registered(self, email: str, password_hash: str) -> None:
        if not self.can_be_upgraded_to_registred():
            raise ValueError("Only a guest user can be upgraded")

        self.email = email
        self.password_hash = password_hash
        self.is_guest = False
