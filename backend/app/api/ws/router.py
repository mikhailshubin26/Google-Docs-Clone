from fastapi import Query, Depends, APIRouter
from typing import Annotated
from starlette.websockets import WebSocket, WebSocketDisconnect
from uuid import UUID
import asyncio

from app.api.ws.connection import WebSocketConnection
from app.api.ws.schemas import parse_incoming_message, IncomingOpMessage, IncomingHeartbeatMessage
from app.application.collab.collab_service import CollabService
from app.core.config import Settings, get_settings
from app.core.di import get_user_repository, get_collab_service
from app.core.security import decode_token, TokenType
from app.domain.exceptions import InvalidTokenError, UserNotFoundError, OperationConflictError, InvalidOperationError
from app.domain.repositories.user import UserRepository
from app.domain.entities.user import User
from app.mappers.operation import operation_from_dict

router = APIRouter(prefix='/ws', tags=['websocket'])
_HEARTBEAT_INTERVAL_SECONDS = 15
_WS_AUTH_FAILED_CODE = 4401

# Валидирует токен (сначала как ACCESS, затем как GUEST)
async def _authenticate(token: str, settings: Settings, user_repo: UserRepository) -> User:
    try:
        user_id = decode_token(token, settings, TokenType.ACCESS)
    except InvalidTokenError:
        user_id = decode_token(token, settings, TokenType.GUEST)

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise UserNotFoundError(user_id)
    return user

# Фоновая задача, продлевающая presence сервера
async def _heartbeat_loop(
        collab_service: CollabService, document_id: UUID, user: User, settings: Settings
) -> None:
    while True:
        await asyncio.sleep(settings.presence_heartbeat_ttl_seconds / 2)
        await collab_service.heartbeat(document_id, user.id, user.display_name)

async def _handle_op(
        message: IncomingOpMessage,
        collab_service: CollabService,
        document_id: UUID,
        user: User,
        connection: WebSocketConnection,
) -> None:
    try:
        operation = operation_from_dict(message.operation)
    except (KeyError, ValueError) as exc:
        await connection.send_json({"type": "error", "detail": f"Malformed operation: {exc}"})
        return

    try:
        new_revision = await collab_service.submit_operation(document_id, user.id, operation)
    except OperationConflictError as exc:
        await connection.send_json({"type": "error", "detail": str(exc), "requierd_resync": True})
        return

    except InvalidOperationError as exc:
        await connection.send_json({"type": "error", "detail": str(exc)})
        return

    await connection.send_json({"type": "ack", "data": new_revision})

# Разбирает и обрабатывает одно входящее сообщение
async def _dispatch(
        raw_message: dict,
        collab_service: CollabService,
        document_id: UUID,
        user: User,
        connection: WebSocketConnection,
) -> None:
    try:
        message = parse_incoming_message(raw_message)
    except ValueError as exc:
        await connection.send_json({"type": "error", "detail": str(exc)})
        return

    if isinstance(message, IncomingOpMessage):
        await _handle_op(message, collab_service, document_id, user, connection)
    elif isinstance(message, IncomingHeartbeatMessage):
        await collab_service.heartbeat(document_id, user.id, user.display_name)


@router.websocket('/documents/{document_id}')
async def document_room(
        websocket: WebSocket,
        document_id: UUID,
        token: Annotated[str, Query()],
        settings: Annotated[Settings, Depends(get_settings)],
        user_repo: Annotated[UserRepository, Depends(get_user_repository)],
        collab_service: Annotated[CollabService, Depends(get_collab_service)]
) -> None:
    try:
        user = await _authenticate(token, settings, user_repo)
    except (InvalidTokenError, UserNotFoundError):
        await websocket.close(code=_WS_AUTH_FAILED_CODE)
        return

    await websocket.accept()
    connection = WebSocketConnection(websocket)

    content, revision = await collab_service.join_room(
        document=document_id,
        user_id=user.id,
        display_name=user.display_name,
        connection=connection
    )
    await connection.send_json({"type": "sync", "content": content, "revision": revision})

    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(collab_service, document_id, user, settings)
    )

    try:
        while True:
            raw_message = await websocket.receive_json()
            await _dispatch(raw_message, collab_service, document_id, user, connection)
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        await collab_service.leave_room(document_id, user.id)