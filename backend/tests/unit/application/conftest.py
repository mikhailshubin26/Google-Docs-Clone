import pytest

from app.application.services.auth_service import AuthService
from app.application.services.document_service import DocumentService
from app.application.services.permission_service import PermissionService
from app.core.config import Settings
from tests.unit.application.fakes import FakeUserRepository, FakeDocumentRepository, FakePermissionRepository


# Минимальный набор настроек, достаточный для тестирования AuthService без реального .env
@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key",
        postgres_db="test",
        postgres_user="test",
        postgres_password="test",
    )

@pytest.fixture
def user_repo() -> FakeUserRepository:
    return FakeUserRepository()

@pytest.fixture
def document_repo() -> FakeDocumentRepository:
    return FakeDocumentRepository()

@pytest.fixture
def permission_repo() -> FakePermissionRepository:
    return FakePermissionRepository()

@pytest.fixture
def auth_service(user_repo: FakeUserRepository, settings: Settings) -> AuthService:
    return AuthService(user_repo=user_repo, settings=settings)

@pytest.fixture
def permission_service(document_repo: FakeDocumentRepository, permission_repo: FakePermissionRepository) -> PermissionService:
    return PermissionService(document_repo=document_repo, permission_repo=permission_repo)

@pytest.fixture
def document_service(document_repo: FakeDocumentRepository, permission_service: PermissionService) -> DocumentService:
    return DocumentService(document_repo=document_repo, permission_service=permission_service)
