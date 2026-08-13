import uuid
from uuid import UUID
from datetime import datetime, timezone

from app.core.config import Settings
from app.core.security import hash_password, create_access_token, create_refresh_token, verify_password, decode_token, \
    TokenType
from app.domain.entities.user import User
from app.domain.exceptions import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError
from app.domain.repositories.user import UserRepository

# Контейнер для пары токенов
class TokenPair:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token

# Бизнес-логика регистрации, входа, гостевого доступа и апгрейда гостя
class AuthService:
    def __init__(self, user_repo: UserRepository, settings: Settings):
        self._user_repo = user_repo
        self._settings = settings

    # Общая точка выпуска пары access+refresh токенов для не-гостя
    def _issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user.id, self._settings, is_guest=False),
            refresh_token=create_refresh_token(user.id, self._settings)
        )


    # Регистрация нового пользователя. Выдаёт пару Токенов
    async def register(self, email: str, password: str, display_name: str) -> TokenPair:
        if await self._user_repo.exists_with_email(email):
            raise UserAlreadyExistsError(email)

        user = User(
            id=uuid.uuid4(),
            display_name=display_name,
            is_guest=False,
            created_at=datetime.now(timezone.utc),
            email=email,
            password_hash=hash_password(password),
        )
        await self._user_repo.create(user)
        return self._issue_tokens(user)

    # Проверяет данные пользователя и выдаёт ему пару токенов
    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._user_repo.get_by_email(email)
        if user is None or user.password_hash is None or verify_password(password, user.password_hash) is False:
            raise InvalidCredentialsError()
        return self._issue_tokens(user)

    # Создаёт временного гостевого пользователя и выдаёт ему пару токенов с коротким TTL
    async def login_as_guest(self, display_name: str) -> TokenPair:
        user = User(
            id=uuid.uuid4(),
            display_name=display_name,
            is_guest=True,
            created_at=datetime.now(timezone.utc),
        )
        await self._user_repo.create(user)
        access_token = create_access_token(user.id, self._settings, is_guest=True)
        return TokenPair(access_token=access_token, refresh_token="") # у гостя нет refresh-токена

    # Превращает гостя в полноценного зарегистрированного пользователя
    async def upgrade_guest(self, user_id: UUID, email: str, password: str) -> TokenPair:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if await self._user_repo.exists_with_email(email):
            raise UserAlreadyExistsError(email)

        user.upgrade_to_registered(email=email, password_hash=hash_password(password))
        await self._user_repo.update(user)
        return self._issue_tokens(user)

    # Обменивает валидный refresh-токен на новую пару токенов
    async def refresh(self, refresh_token: str) -> TokenPair:
        user_id = decode_token(refresh_token, self._settings, TokenType.REFRESH)
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return self._issue_tokens(user)