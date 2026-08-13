# FastAPI-зависимости для аутентификации HTTP-запросов
from http.client import HTTPException
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import Settings, get_settings
from app.core.security import decode_token, TokenType
from app.domain.exceptions import InvalidTokenError, UserNotFoundError
from app.domain.entities.user import User
from app.domain.repositories.user import UserRepository
from app.core.di import get_user_repository

_bearer_scheme = HTTPBearer(auto_error=False)

# Извлекает access-токен текущего пользователя и возвращает его id
async def get_current_user_id(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
        settings: Annotated[Settings, Depends(get_settings)]
) -> UUID:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is missing")

    token = credentials.credentials
    try:
        # Сначала пробуем как обычный access-токен. При неудаче — как гостевой
        return decode_token(token, settings, TokenType.ACCESS)
    except InvalidTokenError:
        try:
            return decode_token(token, settings, TokenType.GUEST)
        except InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

# Возвращает полную доменную сущность User текущего пользователя
async def get_current_user(
        user_id: Annotated[UUID, Depends(get_current_user_id)],
        user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists"
                            ) from UserNotFoundError(user_id=user_id)
    return user