# In-memory fake'и для Collab-слоя: PubSub и PresenceStore
# Живут отдельно от fakes.py, т.к. это не репозитории, а инфраструктурные адаптеры
import asyncio
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID


class FakePubSub:
    def __init__(self) -> None:
        self._subscibers: dict[str, list[asyncio.Queue]] = {}

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        for queue in self._subscibers.get(channel, []):
            await queue.put(message)

    async def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscibers.setdefault(channel, []).append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscibers[channel].remove(queue)

class FakePresenceStore:
    def __init__(self) -> None:
        self._online: dict[UUID, dict[UUID, str]] = {}

    async def mark_online(self, document_id: UUID, user_id: UUID, display_name) -> None:
        self._online.setdefault(document_id, {})[user_id] = display_name

    async def mark_offline(self, document_id: UUID, user_id: UUID) -> None:
        self._online.get(document_id, {}).pop(user_id, None)

    async def list_online(self, document_id: UUID) -> dict[UUID, str]:
        return dict(self._online.get(document_id, {}))