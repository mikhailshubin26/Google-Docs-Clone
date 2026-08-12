from datetime import timedelta, datetime, timezone
import jwt
from enum import StrEnum
from uuid import UUID
from passlib.context import CryptContext

from app.core.config import Settings
from app.domain.exceptions import InvalidTokenError

# обёртка для хэширования
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

"""
Хэширование паролей и работа с JWT-токенами
"""

class TokenType(StrEnum):
    ACCESS="access"
    REFRESH="refresh"
    GUEST="guest"

# хэширование пароля
def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)

# проверка пароля с сохранённым хешем
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)

# создаёт короткоживущий токен для доступа к API; для гостя формируется свой отдельный тип токена
def create_access_token(user_id: UUID, settings: Settings, is_guest: bool = False) -> str:
    token_type = TokenType.GUEST if is_guest else TokenType.ACCESS
    ttl = (
        timedelta(hours=settings.guest_token_expire_hours) if is_guest else timedelta(minutes=settings.access_token_expire_minutes)
    )
    return _encode_token(user_id, token_type, ttl, settings)

# создаёт долгоживущий токен, который потом можно обменять на новый access-токен
def create_refresh_token(user_id: UUID, settings: Settings) -> str:
    ttl = timedelta(days=settings.refresh_token_expire_days)
    return _encode_token(user_id, TokenType.REFRESH, ttl, settings)

# Общая функция, которая собирает и подписывает JWT
def _encode_token(user_id: UUID, token_type: TokenType, ttl: timedelta, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id), # subject — стандартное поле JWT, в данном случае — id пользователя
        "type": token_type.value,
        "iat": now,         # когда выдан
        "exp": now + ttl,   # когда заканчивается
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

# Проверяет подпись токена, срок годности и тип; и возвращает id пользователя
def decode_token(token: str, settings: Settings, excepted_type: TokenType) -> UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenError("Token signature is invalid")

    if payload.get("type") != excepted_type.value:
        raise InvalidTokenError(f"Excepted token type={excepted_type.value}")

    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError):
        raise InvalidTokenError("Token payload is malformed") # Невалидный UUID