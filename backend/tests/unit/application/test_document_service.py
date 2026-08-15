# Юнит-тесты DocumentService: создание, получение, переименовывание, удаление, разграничение прав
import uuid

import pytest

from app.application.services.document_service import DocumentService
from app.domain.entities.permission import Role
from app.domain.exceptions import PermissionDeniedError, DocumentNotFoundError


# Тест создания документа
class TestCreateDocument:

    # Создателю документа автоматически выдаётся роль OWNER
    async def test_create_document_grants_owner_role(self, document_service: DocumentService, permission_repo):
        owner_id = uuid.uuid4()
        document = await document_service.create_document(owner_id=owner_id, title="My doc")

        assert document.title == "My doc"
        assert document.revision == 0
        assert document.content_snapshot == ""

        role = await permission_repo.get_role(document.id, owner_id)
        assert role == Role.OWNER

# Тест получения документа
class TestGetDocument:

    # Владелец документа может его получить
    async def test_owner_can_get_document(self, document_service: DocumentService):
        owner_id = uuid.uuid4()
        created = await document_service.create_document(owner_id=owner_id, title="Doc")
        fetched = await document_service.get_document(created.id, owner_id)
        assert fetched.id == created.id

    # Посторонний не может получить документ
    async def test_stranger_cannot_get_document(self, document_service: DocumentService):
        owner_id = uuid.uuid4()
        stranger_id = uuid.uuid4()
        created = await document_service.create_document(owner_id=owner_id, title="Doc")
        with pytest.raises(PermissionDeniedError):
            await document_service.get_document(created.id, stranger_id)

    # Нельзя получить несуществующий документ
    async def test_get_nonexistent_document(self, document_service: DocumentService):
        user_id = uuid.uuid4()
        with pytest.raises(PermissionDeniedError):
            await document_service.get_document(uuid.uuid4(), user_id)

# Тест переименовывания документа
class TestRenameDocument:

    # Тест, что OWNER может поменять название документа
    async def test_owner_can_rename(self, document_service: DocumentService):
        owner_id = uuid.uuid4()
        created = await document_service.create_document(owner_id=owner_id, title="Old title")
        renamed = await document_service.rename_document(created.id, owner_id, "New title")
        assert renamed.title == "New title"

    # Тест, что EDITOR может поменять название документа
    async def test_editor_can_rename(self, document_service: DocumentService, permission_service):
        owner_id = uuid.uuid4()
        editor_id = uuid.uuid4()
        created = await document_service.create_document(owner_id=owner_id, title="Old title")
        await permission_service.grant_role(created.id, editor_id, Role.EDITOR)

        renamed = await document_service.rename_document(created.id, editor_id, "New title")
        assert renamed.title == "New title"

    # Тест, что VIEWER не может поменять название документа
    async def test_viewer_cannot_rename(self, document_service: DocumentService, permission_service):
        owner_id = uuid.uuid4()
        viewer_id = uuid.uuid4()
        created = await document_service.create_document(owner_id=owner_id, title="Old title")
        await permission_service.grant_role(created.id, viewer_id, Role.VIEWER)

        with pytest.raises(PermissionDeniedError):
            await document_service.rename_document(created.id, viewer_id, "New title")

# Тесты удалений документа
class TestDeleteDocument:

    # OWNER может удалить документ
    async def test_owner_can_delete(self, document_service: DocumentService):
        owner_id = uuid.uuid4()
        created = await document_service.create_document(owner_id=owner_id, title="Doc")
        await document_service.delete_document(created.id, owner_id)

        with pytest.raises(DocumentNotFoundError):
            await document_service.get_document(created.id, owner_id)

    # EDITOR не может удалить документ
    async def test_editor_cannot_delete(self, document_service: DocumentService, permission_service):
        owner_id = uuid.uuid4()
        editor_id = uuid.uuid4()
        created = await document_service.create_document(owner_id=owner_id, title="Doc")
        await permission_service.grant_role(created.id, editor_id, Role.EDITOR)

        with pytest.raises(PermissionDeniedError):
            await document_service.delete_document(created.id, editor_id)

# Тестирование отображения только тех документов, которые принадлежат пользователю
class TestListMyDocuments:
    async def test_list_only_allowed_documents(self, document_service: DocumentService):
        owner_id = uuid.uuid4()
        other_owner_id = uuid.uuid4()
        await document_service.create_document(owner_id=owner_id, title="Mine 1")
        await document_service.create_document(owner_id=owner_id, title="Mine 2")
        await document_service.create_document(owner_id=other_owner_id, title="Not mine")

        documents = await document_service.list_my_documents(owner_id=owner_id)
        assert len(documents) == 2
        assert all(d.owner_id == owner_id for d in documents)