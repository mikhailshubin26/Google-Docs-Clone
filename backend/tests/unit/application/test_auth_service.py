# Юнит-тесты AuthService: регистрация, авторизация, гость, апргрейд гостя, refresh
from uuid import uuid4

import pytest

from app.application.services.auth_service import AuthService
from app.core.config import Settings
from app.core.security import decode_token, TokenType
from app.domain.exceptions import UserAlreadyExistsError, InvalidTokenError, InvalidCredentialsError, UserNotFoundError
from app.domain.repositories.user import UserRepository


# Тестирование регистрации
class TestRegister:

    async def test_register_creates_user_and_return_tokens(self, auth_service: AuthService, settings: Settings):
        tokens = await auth_service.register(
            email="alice@example.com",
            password="password123",
            display_name="Alice",
        )
        assert tokens.access_token
        assert tokens.refresh_token

        user_id = decode_token(tokens.access_token, settings, TokenType.ACCESS)
        assert user_id is not None

    async def test_register_reject_duplicate_email(self, auth_service: AuthService, settings: Settings):
        await auth_service.register(email="bob@example.com", password="password123", display_name="Bob")
        with pytest.raises(UserAlreadyExistsError):
            await auth_service.register(email="bob@example.com", password="password123", display_name="Bob2")

# Тестирование авторизации
class TestLogin:

    async def test_login_with_correct_credentials(self, auth_service: AuthService):
        await auth_service.register(email="carol@example.com", password="password123", display_name="Carol")
        tokens = await auth_service.login(email="carol@example.com", password="password123")
        assert tokens.access_token

    async def test_login_with_wrong_password(self, auth_service: AuthService):
        await auth_service.register(email="dave@example.com", password="password123", display_name="Dave")
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(email="dave@example.com", password="wrong_password")

    async def test_login_with_unknown_email(self, auth_service: AuthService):
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(email="unknown@example.com", password="password123")

# Тестирование гостевого входа
class TestGuestLogin:

    async def test_guest_login_create_guest_user(self, auth_service: AuthService, settings: Settings):
        tokens = await auth_service.login_as_guest(display_name="Guest123")
        assert tokens.access_token
        assert tokens.refresh_token == "" # у гостя нет refresh-токена

        user_id = decode_token(tokens.access_token, settings, TokenType.GUEST)
        assert user_id is not None

# Тестирование апгрейда гостя до полноценного пользователя
class TestUpgradeGuest:

    async def test_upgrade_guest_preserves_user_id(self, auth_service: AuthService, user_repo):
        guest_tokens = await auth_service.login_as_guest(display_name="TempGuest")

        # Достаём id гостя напрямую из fake-репозитория
        guest_user = next(iter(user_repo._users.values()))

        upgraded_tokens = await auth_service.upgrade_guest(
            user_id=guest_user.id, email="upgraded@example.com", password="password123"
        )
        assert upgraded_tokens.refresh_token # теперь должен появиться и refresh-токен

        stored_user = await user_repo.get_by_id(guest_user.id)
        assert stored_user.is_guest is False
        assert stored_user.email == "upgraded@example.com"

    async def test_upgrade_guest_rejects_taken_email(self, auth_service: AuthService, user_repo):
        await auth_service.register(email="taken@example.com", password="password123", display_name="Existing")
        guest_tokens = await auth_service.login_as_guest(display_name="TempGuest")
        guest_user = next(u for u in user_repo._users.values() if u.is_guest)

        with pytest.raises(UserAlreadyExistsError):
            await auth_service.upgrade_guest(
                user_id=guest_user.id, email="taken@example.com", password="password123"
            )

    async def test_upgrade_nonexistent_user_raises(self, auth_service: AuthService):
        with pytest.raises(UserNotFoundError):
            await auth_service.upgrade_guest(
                user_id=uuid4, email="ghost@example.com", password="password123"
            )

# Тестирование обновления токенов
class TestRefresh:

    async def test_refresh_returns_new_tokens(self, auth_service: AuthService):
        tokens = await auth_service.register(email="erin@example.com", password="password123", display_name="Erin")
        new_tokens = await auth_service.refresh(tokens.refresh_token)
        assert new_tokens.access_token
        assert new_tokens.refresh_token