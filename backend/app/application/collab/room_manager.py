from typing import Protocol, Any
from uuid import UUID


class Connection(Protocol):
    async def send_json(self, data: dict[str, Any]) -> None:
        ...

# Локальный реестр WebSocket подключений по комнатам (документам)
class RoomManager:
    def __init__(self) -> None:
        # document_id -> {user_id: Connection}
        self._rooms: dict[UUID, dict[UUID, Connection]] = {}

    # Добавляет соединение пользователя в "комнату" документу
    def join(self, document_id: UUID, user_id: UUID, connection: Connection) -> None:
        room = self._rooms.setdefault(document_id, {})
        room[user_id] = connection

    # Убирает пользователя из команты. Если комната опустела — удаляет её из словаря целиком
    def leave(self, document_id: UUID, user_id: UUID) -> None:
        room = self._rooms.get(document_id)
        if room is None:
            return
        room.pop(user_id, None)
        if not room:
            del self._rooms[document_id]

    # Возвращает все подключения комнаты
    def get_connection(self, document_id: UUID) -> dict[UUID, Connection]:
        return self._rooms.get(document_id, {})

    # Рассылка сообщения всем локальным подключением в комнате.
    async def broadcast_local(
            self, document_id: UUID, message: dict[str, Any], exclude_user_id: UUID | None = None
    ) -> None:
        for user_id, connection in self.get_connection(document_id).items():
            if user_id == exclude_user_id:
                continue
            await connection.send_json(message)