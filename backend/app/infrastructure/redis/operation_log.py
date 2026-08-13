from uuid import UUID

from redis.asyncio import Redis

from app.domain.ot import operation
from app.domain.ot.operation import Operation
from app.mappers.operation import operation_to_json, operation_from_json

# Реализация OperationLogRepository (интерфейс из domain/repositories/operation_log.py)
class RedisOperationLogRepository:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    # формирует ключ Redis Stream для лога операций
    def _stream_key(self, document_id: UUID) -> str:
        return f"oplog:{document_id}"

    # добавляет операцию в конец потока
    async def append(self, document_id: UUID, revision: int, operation: Operation) -> None:
        stream_key = self._stream_key(document_id)
        payload = operation_to_json(operation)
        await self._redis.xadd(
            stream_key,
            {"revision": str(revision), "operation": payload},
        )

    # возвращает операции с revision > since_revision
    async def get_operations_since(self, document_id: UUID, since_revision: int) -> list[Operation]:
        stream_key = self._stream_key(document_id)
        entries = await self._redis.xrange(stream_key, min="-", max="+")

        operations: list[Operation] = []
        for _, fields in entries:
            revision = int(fields["revision"])
            if revision > since_revision:
                operations.append(operation_from_json(fields["operation"]))
        return operations

    # возрвщает номер последней ревизии в логе. Если лог пустой: возвращает 0
    async def get_latest_revision(self, document_id: UUID) -> int:
        stream_key = self._stream_key(document_id)
        entries = await self._redis.xrevrange(stream_key, count=1)
        if not entries:
            return 0
        _, fields = entries[0]
        return int(fields["revision"])

    """
    Удаляет/архивирует записи лога вплоть до указанной ревизии.
    Вызывается после того, как application-слой схлопнул операции в новый снапшот
    """
    async def compact(self, document_id: UUID, up_to_revision: int) -> None:
        stream_key = self._stream_key(document_id)
        entries = await self._redis.xrange(stream_key, min="-", max="+")
        ids_to_delete = [
            entry_id
            for entry_id, fields in entries
            if int(fields["revision"]) <= up_to_revision
        ]
        if ids_to_delete:
            await self._redis.xdel(stream_key, *ids_to_delete)