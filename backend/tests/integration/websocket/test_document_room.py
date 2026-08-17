import asyncio
import uuid
from datetime import datetime, timezone

import pytest
import anyio
from starlette.websockets import WebSocketDisconnect

from app.core.config import get_settings
from app.core.security import create_access_token
from app.domain.entities.permission import Permission, Role
from app.domain.entities.user import User
from tests.integration.websocket.conftest import seed_user_and_document

"""
E2E тест WS-комнаты через TestClient
"""

class TestDocumentRoomConnection:

    def test_valid_token_receives_sync_message(
        self, client, fake_user_repo, fake_document_repo, fake_permission_repo
    ):
        user, document = seed_user_and_document(fake_user_repo, fake_document_repo, fake_permission_repo)
        settings = get_settings()
        token = create_access_token(user.id, settings, is_guest=False)

        with client.websocket_connect(f"/ws/documents/{document.id}?token={token}") as ws:
            message = ws.receive_json()
            assert message["type"] == "sync"
            assert message["content"] == "Hello"
            assert message["revision"] == 0

    def test_invalid_token_closes_connection(self, client, fake_document_repo):
        document_id = uuid.uuid4()

        try:
            with pytest.raises(Exception):
                with client.websockets_connect(f"/ws/documents/{document_id}?token=not-a-real-token") as ws:
                    pass
                assert False, "expected connection to be rejected"
        except WebSocketDisconnect as exc:
            assert exc.code == 4401

class TestDocumentRoomCollaboration:

    # Клиент A подключается, отправляет операцию. Клиент B (уже подключенный) должен получить op_broadcast
    def test_two_clients_exchange_operations(
            self, client, fake_user_repo, fake_document_repo, fake_permission_repo
    ):
        user_a, document = seed_user_and_document(fake_user_repo, fake_document_repo, fake_permission_repo)
        settings = get_settings()
        token_a = create_access_token(user_a.id, settings, is_guest=False)

        async def _seed_second_user():
            now = datetime.now(timezone.utc)
            user_b = User(
                id=uuid.uuid4(),
                display_name="Bob",
                is_guest=True,
                created_at=now,
            )
            await fake_user_repo.create(user_b)
            await fake_permission_repo.grant(
                Permission(
                    document_id=document.id,
                    user_id=user_b.id,
                    role=Role.EDITOR,
                    granted_at=now
                )
            )
            return user_b

        user_b = asyncio.run(_seed_second_user())
        token_b = create_access_token(user_b.id, settings, is_guest=True)

        with client.websocket_connect(f"/ws/documents/{document.id}?token={token_a}") as ws_a:
            ws_a.receive_json() # sync-сообщение клиента A

            with client.websocket_connect(f"/ws/documents/{document.id}?token={token_b}") as ws_b:
                ws_b.receive_json() # sync-сообщение клиента B

                # Клиент A: "Hello" -> "Hello!"
                ws_a.send_json({
                    "type": "op",
                    "operation": {
                        "components": [
                            {"type": "retain", "count": 5},
                            {"type": "insert", "text": "!"},
                        ],
                        "client_id": str(user_a.id),
                        "base_revision": 0,
                    },
                })

                ack = ws_a.receive_json()
                print("ACK CONTENT:", ack)
                assert ack["type"] == "ack"
                assert ack["data"] == 1

                broadcast = ws_b.receive_json()
                assert broadcast["type"] == "op_broadcast"
                assert ack["data"] == 1