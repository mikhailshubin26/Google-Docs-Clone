# Юнит-тесты PermissionService: проверка текущей роли, проверка разрешений, проверка отзывания роли

import uuid
from datetime import timezone, datetime

import pytest

from app.application.services.permission_service import PermissionService
from app.domain.entities.document import Document
from app.domain.entities.permission import Role
from app.domain.exceptions import PermissionDeniedError


def _make_document(owner_id) -> Document:
    now = datetime.now(timezone.utc)
    return Document(
        id=uuid.uuid4(),
        owner_id=owner_id,
        title="Test doc",
        content_snapshot="",
        revision=0,
        created_at=now,
        updated_at=now,
    )


# Получение текущей роли
class TestGetEffectiveRole:

    # Создателю документа автоматически даётся роль владельца
    async def test_owner_has_owner_role_without_explicit_grant(
            self, permission_service: PermissionService, document_repo):
        owner_id = uuid.uuid4()
        document = _make_document(owner_id)
        await document_repo.create(document)

        role = await permission_service.get_effective_role(document.id, owner_id)
        assert role == Role.OWNER

    # У постороннего человека нет никакой роли на документ
    async def test_stranger_has_no_role(self, permission_service: PermissionService, document_repo):
        owner_id = uuid.uuid4()
        stranger_id = uuid.uuid4()
        document = _make_document(owner_id)
        await document_repo.create(document)

        role = await permission_service.get_effective_role(document.id, stranger_id)
        assert role is None

    # Проверка выдачи роли
    async def test_granted_role_is_respected(self, permission_service: PermissionService, document_repo):
        owner_id = uuid.uuid4()
        editor_id = uuid.uuid4()
        document = _make_document(owner_id)
        await document_repo.create(document)
        await permission_service.grant_role(document.id, editor_id, Role.EDITOR)

        role = await permission_service.get_effective_role(document.id, editor_id)
        assert role == Role.EDITOR

# Проверка соответствия роли запрашиваемым возможностям
class TestCheckPermission:

    # Роль соответствует требованиям
    async def test_passes_when_role_satisfies_requirements(
            self, permission_service: PermissionService, document_repo
    ):
        owner_id = uuid.uuid4()
        document = _make_document(owner_id)
        await document_repo.create(document)

        await permission_service.check_permission(document.id, owner_id, Role.VIEWER)

    # Роли недостаточно
    async def test_raises_when_role_insufficient(self, permission_service: PermissionService, document_repo):
        owner_id = uuid.uuid4()
        viewer_id = uuid.uuid4()
        document = _make_document(owner_id)
        await document_repo.create(document)
        await permission_service.grant_role(document.id, viewer_id, Role.VIEWER)

        with pytest.raises(PermissionDeniedError):
            await permission_service.check_permission(document.id, viewer_id, Role.EDITOR)

    # Роли нет вообще
    async def test_raises_with_no_role_at_all(self, permission_service: PermissionService, document_repo):
        owner_id = uuid.uuid4()
        stranger_id = uuid.uuid4()
        document = _make_document(owner_id)
        await document_repo.create(document)

        with pytest.raises(PermissionDeniedError):
            await permission_service.check_permission(document.id, stranger_id, Role.VIEWER)

class TestRevokeRole:

    async def test_revoke_removes_access(self, permission_service: PermissionService, document_repo):
        owner_id = uuid.uuid4()
        editor_id = uuid.uuid4()
        document = _make_document(owner_id)
        await document_repo.create(document)
        await permission_service.grant_role(document.id, editor_id, Role.EDITOR)

        await permission_service.revoke_role(document.id, editor_id)

        role = await permission_service.get_effective_role(document.id, editor_id)
        assert role is None