from pydantic import BaseModel
from typing import Literal, Any


class IncomingOpMessage(BaseModel):
    type: Literal["op"]
    operation: dict[str, Any]

class IncomingHeartbeatMessage(BaseModel):
    type: Literal["heartbeat"]

# Оперделяет тип входящего сообщения и валидирует его
def parse_incoming_message(raw: dict[str, Any]) -> IncomingOpMessage | IncomingHeartbeatMessage:
    message_type = raw["type"]
    if message_type == "op":
        return IncomingOpMessage.model_validate(raw)
    if message_type == "heartbeat":
        return IncomingHeartbeatMessage.model_validate(raw)
    raise ValueError(f"Unknown message type: {message_type}")