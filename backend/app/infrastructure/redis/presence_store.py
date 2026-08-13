from redis.asyncio import Redis
from uuid import UUID

# хранилище присутствия пользователей в документе
class RedisPresenceStore:
    def __init__(self, redis: Redis, ttl_seconds: int):
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    # формуирует ключ <document_id>:<user_id>
    def _key(self, document_id: UUID, user_id: UUID) -> str:
        return f"{document_id}:{user_id}"

    # формирует паттерн для поиска всех присутствующих в документе
    def _pattern(self, document_id: UUID) -> str:
        return f"{document_id}:*"

    # отметить пользователя, как присутствующего в документе
    async def mark_online(self, document_id: UUID, user_id: UUID, display_name: str) -> None:
        key = self._key(document_id, user_id)
        await self._redis.set(key, display_name, ex=self._ttl_seconds)

    # убрать пользователя из presence (вызывается при выходе из документа)
    async def mark_offline(self, document_id: UUID, user_id: UUID) -> None:
        key = self._key(document_id, user_id)
        await self._redis.delete(key)

    # возвращает всех, кто сейчас в документе
    async def list_online(self, document_id: UUID) -> dict[UUID, str]:
        online: dict[UUID, str] = {}
        pattern = self._pattern(document_id)
        async for key in self._redis.scan_iter(match=pattern):
            user_id_str = key.split(":")[-1]
            display_name = await self._redis.get(key)
            if display_name is not None:
                online[UUID(user_id_str)] = display_name
        return online