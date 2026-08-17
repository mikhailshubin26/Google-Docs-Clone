import asyncio
from datetime import timezone, datetime
import uuid
import pytest

from app.application.collab.collab_service import CollabService
from app.application.collab.room_manager import RoomManager
from app.application.ot.controller import OTController
from app.domain.entities.document import Document
from app.domain.ot.operation import Operation, Retain, Insert
from tests.unit.application.fakes import FakeDocumentRepository, FakeOperationLogRepository
from tests.unit.application.fakes_collab import FakePubSub, FakePresenceStore
from tests.unit.application.test_room_manager import FakeConnection

"""
Юнит-тесты CollabService
"""

@pytest.fixture
def ot_controller(document_repo) -> OTController:
    return OTController(
        document_repo=document_repo,
        operation_log_repo=FakeOperationLogRepository(),
        compact_threshold=1000,
    )

@pytest.fixture
def collab_service(ot_controller) -> CollabService:
    return CollabService(
        ot_controller=ot_controller,
        room_manager=RoomManager(),
        pubsub=FakePubSub(),
        presence_store=FakePresenceStore(),
    )

@pytest.fixture
def document_repo() -> FakeDocumentRepository:
    return FakeDocumentRepository()

async def _make_document(document_repo: FakeDocumentRepository, content: str = "Hello") -> Document:
    now = datetime.now(timezone.utc)
    document = Document(
        uuid.uuid4(),
        owner_id=uuid.uuid4(),
        title="Doc",
        content_snapshot=content,
        revision=0,
        created_at=now,
        updated_at=now,
    )
    await document_repo.create(document)
    return document

class TestJoinRoom:

    async def test_join_returns_current_content_and_marks_presence(self, collab_service, document_repo):
        document = await _make_document(document_repo, content="Hello")
        user_id = uuid.uuid4()

        content, revision = await collab_service.join_room(document.id, user_id, "Alice", FakeConnection())
        try:
            assert content == "Hello"
            assert revision == 0
            online = await collab_service.list_online(document.id)
            assert online == {user_id: "Alice"}
        finally:
            await collab_service.leave_room(document.id, user_id)

class TestLeaveRoom:

    async def test_leave_clears_presence(self, collab_service, document_repo):
        document = await _make_document(document_repo, content="Hello")
        user_id = uuid.uuid4()
        await collab_service.join_room(document.id, user_id, "Bob", FakeConnection())
        await collab_service.leave_room(document.id, user_id)
        online = await collab_service.list_online(document.id)
        assert online == {}

class TestSubmitOperation:

    async def test_broadcasts_to_other_local_connections(self, collab_service, document_repo):
        document = await _make_document(document_repo, content="Hello")
        author_id, other_id = uuid.uuid4(), uuid.uuid4()
        author_conn, other_conn = FakeConnection(), FakeConnection()

        await collab_service.join_room(document.id, author_id, "Author", author_conn)
        await collab_service.join_room(document.id, other_id, "Other", other_conn)

        try:
            # даём event loop'у время доставить сообщение
            await asyncio.sleep(0.05)

            # Диагностика пробелемы
            # task = collab_service._subscriber_tasks.get(document.id)
            # assert task is not None, "subscriber task was never created"
            # assert not task.done(), f"subscriber task finished early: {task.exception() if task.done() else None}"

            op = Operation(components=(Retain(5), Insert("!")), client_id=str(author_id), base_revision=0)
            new_revision = await collab_service.submit_operation(document.id, author_id, op)

            await asyncio.sleep(0.05)

            assert new_revision == 1
            assert author_conn.sent == []
            assert len(other_conn.sent) == 1
            assert other_conn.sent[0]["type"] == "op_broadcast"
            assert other_conn.sent[0]["revision"] == 1

        finally:
            await collab_service.leave_room(document.id, author_id)
            await collab_service.leave_room(document.id, other_id)