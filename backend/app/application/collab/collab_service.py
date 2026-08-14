import asyncio
from uuid import UUID

from app.application.collab.room_manager import RoomManager, Connection
from app.application.interfaces.pubsub import PubSub
from app.application.ot.controller import OTController
from app.domain.ot.operation import Operation
from app.infrastructure.redis.presence_store import RedisPresenceStore
from app.mappers.operation import operation_to_dict


# Формирует имя Pub/Sub канала для документа
def _channel_for(document_id: UUID) -> str:
    return f"document_ops:{document_id}"

"""
Оркестр. Связывает OT-логику (OTController), локальную рассылку (RoomManager),
межпроцессную рассылку (PubSub), и тех, кто онлайн (PresenceStore)
"""
class CollabService:
    def __init__(
            self,
            ot_controller: OTController,
            room_manager: RoomManager,
            pubsub: PubSub,
            presence_store: RedisPresenceStore,
    ) -> None:
        self._ot_controller = ot_controller
        self._room_manager = room_manager
        self._pubsub = pubsub
        self._presence_store = presence_store
        self._subscriber_tasks: dict[UUID, asyncio.Task] = {} # Pub/Sub канал документа

    # Слушает PubSub канал документа и рассылает пришедшие сообщения всем локальным соединеням
    async def _listen_channel(self, document_id: UUID) -> None:
        channel = _channel_for(document_id)
        async for message in self._pubsub.subscribe(channel):
            author_id = UUID(message["author_id"])
            await self._room_manager.broadcast_local(
                document_id, message, exclude_user_id=author_id
            )

    # Запускает фоновую задачу подписки на канал документа
    def _ensure_subsciber(self, document_id: UUID) -> None:
        if document_id not in self._subscriber_tasks:
            return
        task = asyncio.create_task(self._listen_channel(document_id))
        self._subscriber_tasks[document_id] = task

    # Останавливаем фоновую задачу подписки, если она была запущена
    def _cancel_subscriber(self, document_id: UUID) -> None:
        task = self._subscriber_tasks.pop(document_id, None)
        if task is not None:
            task.cancel()

    # Подключает пользователя к комнате документа. Возвращает актуальное состояние документа
    async def join_room(
            self, document_id: UUID, user_id: UUID, display_name: str, connection: Connection
    ) -> tuple[str, int]:
        self._room_manager.join(document_id, user_id, connection)
        await self._presence_store.mark_online(document_id, user_id, display_name) # Отмечает присутствие пользователя
        self._ensure_subscriber(document_id) # Запускает подписку на Pub/Sub канал документа
        content, revision = await self._ot_controller.get_current_state(document_id)
        return content, revision

    # Отключает пользоваптеля от комнаты. Вызывается при закрытии WS-соединения
    async def leave_room(self, document_id: UUID, user_id: UUID) -> None:
        self._room_manager.leave(document_id, user_id)
        await self._presence_store.mark_offline(document_id, user_id) # Отмечает отсутствие пользователя в документе

        # Останавливаем подписку на Redis-канал, если пользователей не осталось
        if not self._room_manager.get_connection(document_id):
            self._cancel_subscriber(document_id)

    """
    Применяет операцию через OTController. Далее публикует результат в PubSub на рассылку по локальным
    WS-соединеням.
    """
    async def submit_operation(
            self, document_id: UUID, user_id: UUID, operation: Operation
    ) -> int:
        transformed_op, new_revision = await self._ot_controller.submit_operation(document_id, operation)
        message = {
            "type": "op_broadcast",
            "operation": operation_to_dict(transformed_op),
            "revision": new_revision,
            "author_id": str(user_id),
        }
        await self._pubsub.publish(_channel_for(document_id), message)
        return new_revision

    # Продливаем TTL-присутствия пользователя
    async def heartbeat(self, document_id: UUID, user_id: UUID, display_name: str) -> None:
        await self._presence_store.mark_online(document_id, user_id, display_name)

    # Возвращает список тех, кто сейчас в документе
    async def list_online(self, document_id: UUID) -> dict[UUID, str]:
        return await self._presence_store.list_online(document_id)