import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.application.collab.collab_service import CollabService
from app.application.collab.room_manager import RoomManager
from app.application.ot.controller import OTController
from app.core.di import get_user_repository, get_permission_repository, get_document_repository, get_collab_service
from app.domain.entities.document import Document
from app.domain.entities.permission import Permission, Role
from app.domain.entities.user import User
from app.main import app
from tests.unit.application.fakes import FakeUserRepository, FakeDocumentRepository, FakeOperationLogRepository, \
    FakePermissionRepository
from tests.unit.application.fakes_collab import FakePubSub, FakePresenceStore


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
def test_collab_service(fake_document_repo) -> CollabService:
    ot_controller = OTController(
        document_repo=fake_document_repo,
        operation_log_repo=FakeOperationLogRepository(),
        compact_threshold=1000,
    )
    return CollabService(
        ot_controller=ot_controller,
        room_manager=RoomManager(),
        pubsub=FakePubSub(),
        presence_store=FakePresenceStore(),
    )

@pytest.fixture
def client(fake_user_repo, fake_permission_repo, fake_document_repo, test_collab_service):
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repo
    app.dependency_overrides[get_document_repository] = lambda: fake_document_repo
    app.dependency_overrides[get_permission_repository] = lambda: fake_permission_repo
    app.dependency_overrides[get_collab_service] = lambda: test_collab_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

def seed_user_and_document(
    fake_user_repo, fake_document_repo, fake_permission_repo, is_guest: bool = False
) -> tuple[User, Document]:
    async def _seed() -> tuple[User, Document]:
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            display_name='Alice',
            is_guest=is_guest,
            created_at=now,
            email='alice@example.com',
            password_hash=None if is_guest else "hash",
        )
        await fake_user_repo.create(user)

        document = Document(
            id=uuid.uuid4(),
            owner_id=user.id,
            title='Doc',
            content_snapshot="Hello",
            revision=0,
            created_at=now,
            updated_at=now,
        )
        await fake_document_repo.create(document)
        await fake_permission_repo.grant(
            Permission(document_id=document.id, user_id=user.id, role=Role.OWNER, granted_at=now),
        )
        return user, document

    return asyncio.run(_seed())