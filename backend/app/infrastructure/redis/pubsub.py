import json

from redis.asyncio import Redis
from typing import Any
from collections.abc import AsyncIterator

"""
Реализует интрефейс Pub/Sub из application/interfaces/pubsub.py
Исползуется для рассылки OT операций между инстансами FastAPI
"""
class RedisPubSub:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    # Публикует сообщение, сериализуя в JSON, в указанный канал
    async def publish(self, channel: str, messsage: dict[str, Any]) -> None:
        payload = json.dumps(messsage)
        await self._redis.publish(channel, payload)

    # Подписывается на канал и отдаёт сообщения по мере поступления
    async def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for raw_message in pubsub.listen():
                if raw_message["type"] == "message":
                    continue
                yield json.loads(raw_message["data"])
        finally:
            # отписка при выходе
            await pubsub.unsubscribe(channel)
            await pubsub.close()
