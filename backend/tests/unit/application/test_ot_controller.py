import uuid
from datetime import timezone, datetime

import pytest

from app.application.ot.controller import OTController
from app.domain.entities.document import Document
from app.domain.exceptions import OperationConflictError
from app.domain.ot.operation import Operation, Retain, Insert
from tests.unit.application.fakes import FakeDocumentRepository, FakeOperationLogRepository


@pytest.fixture
def document_repo() -> FakeDocumentRepository:
    return FakeDocumentRepository()

@pytest.fixture
def operation_log_repo() -> FakeOperationLogRepository:
    return FakeOperationLogRepository()

@pytest.fixture
def controller(document_repo, operation_log_repo) -> OTController:
    return OTController(document_repo=document_repo, operation_log_repo=operation_log_repo, compact_threshold=1000)

async def _make_document(document_repo: FakeDocumentRepository, content: str = "") -> Document:
    now = datetime.now(timezone.utc)
    document = Document(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        title="Doc",
        content_snapshot=content,
        revision=0,
        created_at=now,
        updated_at=now,
    )
    await document_repo.create(document)
    return document

class TestGetCurrentState:

    async def test_returns_snapshot_when_log_is_empty(self, controller, document_repo):
        document = await _make_document(document_repo, "Hello World")
        content, revision = await controller.get_current_state(document.id)
        assert content == "Hello World"
        assert revision == 0

    async def test_replays_pending_operation_on_snapshot(self, controller, document_repo, operation_log_repo):
        document = await _make_document(document_repo, "Hello")
        op = Operation(components=(Retain(5), Insert("!")), client_id="A", base_revision=0)
        await operation_log_repo.append(document.id, 1, op)
        content, revision = await controller.get_current_state(document.id)
        assert content == "Hello!"
        assert revision == 1

class TestSubmitOperation:

    async def test_first_operation_applies_cleanly(self, controller, document_repo):
        document = await _make_document(document_repo, "Hello")
        op = Operation(components=(Retain(5), Insert(" world")), client_id="A", base_revision=0)

        transformed_op, new_revision = await controller.submit_operation(document.id, op)

        assert new_revision == 1
        content, revision = await controller.get_current_state(document.id)
        assert content == "Hello world"
        assert revision == 1

    # Два клиента шлют конкурентные операции от одной и той же ревизии
    async def test_concurrent_operations_both_apply_via_transform(self, controller, document_repo):
        document = await _make_document(document_repo, "Hello world")
        op_a = Operation(components=(Retain(11), Insert("!")), client_id="A", base_revision=0)
        op_b = Operation(components=(Retain(5), Insert(","), Retain(6)), client_id="B", base_revision=0)
        await controller.submit_operation(document.id, op_a)
        await controller.submit_operation(document.id, op_b)

        content, revision = await controller.get_current_state(document.id)
        assert content == "Hello, world!"
        assert revision == 2

    async def test_operation_from_the_future_raises_conflict(self, controller, document_repo):
        document = await _make_document(document_repo, "Hello")
        op = Operation(components=(Retain(5), Insert("!")), client_id="A", base_revision=99)

        with pytest.raises(OperationConflictError):
            await controller.submit_operation(document.id, op)
