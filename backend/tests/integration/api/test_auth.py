from http import HTTPStatus

from httpx import AsyncClient

class TestRegisterEndpoint:

    async def test_register_returns_token(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "password": "password123",
                "display_name": "Alice"},
        )
        assert response.status_code == 201
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_register_rejects_dublicate_email(self, client: AsyncClient):
        payload = {"email": "bob@example.com", "password": "password123", "display_name": "Bob"}
        await client.post("/api/v1/auth/register", json=payload)
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bob@example.com",
                "password": "password123",
                "display_name": "Bob2"
            }
        )
        assert response.status_code == 409

    async def test_register_rejects_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "carol@example.com",
                "password": "short",
                "display_name": "Carol"
            }
        )
        assert response.status_code == 422 # Pydantic-валидация

    async def test_register_rejects_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "display_name": "Dave"
            }
        )
        assert response.status_code == 422

class TestLoginEndpoint:

    async def test_login_with_correct_credentials(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "erin@example.com",
                "password": "password123",
                "display_name": "Erin"
            }
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "erin@example.com",
                "password": "password123",
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_with_wrong_password_returns_401(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "frank@example.com",
                "password": "password123",
                "display_name": "Frank"
            }
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "frank@example.com",
                "password": "wrong-password",
            }
        )
        assert response.status_code == 401

    async def test_login_with_unknown_email_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "unknown@example.com",
                "password": "placholder",
            }
        )
        assert response.status_code == 401

class TestGuestEndpoint:

    async def test_guest_login_returns_access_token_without_refresh(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/guest",
            json={"display_name": "GuestUser"}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["access_token"]
        assert body["refresh_token"] == ""

class TestUpgradeEndpoint:

    async def test_upgrade_guest_to_registrated(self, client: AsyncClient):
        guest_response = await client.post("/api/v1/auth/guest", json={"display_name": "TempGuest"})
        guest_token = guest_response.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/upgrade",
            json={"email": "upgrade@example.com", "password": "password123"},
            headers={"Authorization": f"Bearer {guest_token}"}
        )
        assert response.status_code == 200
        assert response.json()["refresh_token"] # Проверяем, что появились refresh-токены

    async def test_upgrade_without_token_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/upgrade",
            json={"email": "nobody@example.com", "password": "password123"}
        )
        assert response.status_code == 401

class TestRefreshEndpoint:

    async def test_refresh_returns_new_tokens(self, client: AsyncClient):
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "grace@example.com",
                "password": "password123",
                "display_name": "Grace"
            }
        )
        refresh_token = register_response.json()["refresh_token"]

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        assert response.json()["access_token"]

    async def test_refresh_without_token_returns_401(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
        assert response.status_code == 401