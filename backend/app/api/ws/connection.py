from starlette.websockets import WebSocket
from typing import Any


class WebSocketConnection:
    def __init__(self, websocket: WebSocket):
        self._websocket = websocket

    async def send_json(self, data: dict[str, Any]) -> None:
        await self._websocket.send_json(data)