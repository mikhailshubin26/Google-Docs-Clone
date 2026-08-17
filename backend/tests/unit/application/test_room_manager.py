import uuid
from typing import Any

from app.application.collab.room_manager import RoomManager

"""
Юнит-тесты RoomManager
"""

# Собирает отправленные сообщения в список. Вместо реальных WebSocket
class FakeConnection:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, data: dict[str, Any]) -> None:
        self.sent.append(data)

class TestJoinLeave:

    def test_join_registers_connection(self):
        manager = RoomManager()
        document_id, user_id = uuid.uuid4(), uuid.uuid4()
        connection = FakeConnection()

        manager.join(document_id, user_id, connection)
        assert manager.get_connection(document_id) == {user_id: connection}

    def test_leave_removes_connection(self):
        manager = RoomManager()
        document_id, user_id = uuid.uuid4(), uuid.uuid4()
        manager.join(document_id, user_id, FakeConnection())
        manager.leave(document_id, user_id)
        assert manager.get_connection(document_id) == {}

    def test_leaves_removes_empty_room_entirely(self):
        manager = RoomManager()
        document_id, user_id = uuid.uuid4(), uuid.uuid4()
        manager.join(document_id, user_id, FakeConnection())
        manager.leave(document_id, user_id)

        assert document_id not in manager._rooms

    def test_leave_on_unknown_room_does_not_raise(self):
        manager = RoomManager()
        manager.leave(uuid.uuid4(), uuid.uuid4()) # Не должна вызваться ошибка

class TestBroadcastLocal:

    async def test_broadcasts_to_all_except_included(self):
        manager = RoomManager()
        document_id, author_id, other_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        author_conn, other_conn = FakeConnection(), FakeConnection()

        manager.join(document_id, author_id, author_conn)
        manager.join(document_id, other_id, other_conn)

        message = {"type": "op_broadcast", "revision": 1}
        await manager.broadcast_local(document_id, message, exclude_user_id=author_id)

        assert author_conn.sent == []
        assert other_conn.sent == [message]
