import pytest
from httpx import ASGITransport, AsyncClient

from app.core.di import get_user_repository, get_document_repository, get_permission_repository
from app.main import app
from tests.unit.application.fakes import FakeUserRepository, FakeDocumentRepository, FakePermissionRepository

"""
Fixtures для интеграционных тестов REST API:
Поднимает настоящее Fast API приложение и HTTP-стек
"""

@pytest.fixture
def fake_user_repo() -> FakeUserRepository:
    return FakeUserRepository()

@pytest.fixture
def fake_document_repo() -> FakeDocumentRepository:
    return FakeDocumentRepository()

@pytest.fixture
def fake_permission_repo() -> FakePermissionRepository:
    return FakePermissionRepository()

@pytest.fixture
async def client(
        fake_user_repo: FakeUserRepository,
        fake_document_repo: FakeDocumentRepository,
        fake_permission_repo: FakePermissionRepository,
):
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repo
    app.dependency_overrides[get_document_repository] = lambda: fake_document_repo
    app.dependency_overrides[get_permission_repository] = lambda: fake_permission_repo

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post("/api/v1/auth/register",
                                 json={
                                     "email": "fixture_user@example.com",
                                     "password": "password123",
                                     "display_name": "Fixture User",
                                 })
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}