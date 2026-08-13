from typing import Protocol, Any
from collections.abc import AsyncIterator

# абстрактный контракт pubsub-канала для рассылки сообщений между инстансами приложения
class PubSub(Protocol):
    # публикация сообщений в канал
    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        ...

    # подписка на канал
    async def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        ...