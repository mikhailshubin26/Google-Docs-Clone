from typing import Annotated

from redis.asyncio import Redis
from fastapi import Depends

from app.application.collab.collab_service import CollabService
from app.application.collab.room_manager import RoomManager
from app.application.interfaces.exporter import Exporter
from app.application.interfaces.pubsub import PubSub
from app.application.ot.controller import OTController
from app.application.services.export_service import ExportService
from app.core.config import Settings, get_settings

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from collections.abc import AsyncGenerator

from app.domain.repositories.document import DocumentRepository
from app.domain.repositories.operation_log import OperationLogRepository
from app.domain.repositories.permission import PermissionRepository
from app.domain.repositories.user import UserRepository

from app.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from app.infrastructure.db.repositories.document import SqlAlchemyDocumentRepository
from app.infrastructure.db.repositories.permission import SqlAlchemyPermissionRepository
from app.infrastructure.export.docx_exporter import DocxExporter
from app.infrastructure.export.txt_export import TxtExporter
from app.infrastructure.redis.operation_log import RedisOperationLogRepository
from app.application.services.auth_service import AuthService
from app.application.services.permission_service import PermissionService
from app.application.services.document_service import DocumentService
from app.infrastructure.redis.presence_store import RedisPresenceStore
from app.infrastructure.redis.pubsub import RedisPubSub

# ======================================================================================
# Слой 1: низкоуровневые ресурсы (engine БД, Redis-клиент); Создаются один раз на процесс
# ======================================================================================

_engine = None
_session_factory = None
_redis_client: Redis | None = None
_room_manager: RoomManager | None = None

# Создаёт при первом вызове и возвращает SQLAlchemy engine — пул соединений с Postgres
def get_engine(settings: Annotated[Settings, Depends(get_settings)]):
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            echo=settings.db_echo,
        )
    return _engine

# Возвращает фабрику сессий БД
def get_session_factory(engine=Depends(get_engine)):
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory

# Создаёт отдельную сессию БД на каждый запрос и гарантировано закрывает её после
async def get_db_session(session_factory = Depends(get_session_factory))->AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session

# Один раз создаёт и возвращает клиент Redis
def get_redis(settings: Annotated[Settings, Depends(get_settings)]) -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client

# Один раз создаёт и возвращает RoomManager
def get_room_manager() -> RoomManager:
    global _room_manager
    if _room_manager is None:
        _room_manager = RoomManager()
    return _room_manager

# ======================================================================================
# Слой 2: репозитории. Интерфейс подключается к реализации на SQLAlchemy/Redis
# ======================================================================================

# Отдаёт реализацию UserRepository поверх текущей сессии БД
def get_user_repository(
        session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    return SqlAlchemyUserRepository(session)

# Отдаёт реализацию PermissionRepository поверх текущей сессии БД
def get_permission_repository(
        session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PermissionRepository:
    return SqlAlchemyPermissionRepository(session)

# Отдаёт реализацию DocumentRepository поверх текущей сессии БД
def get_document_repository(
        session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentRepository:
    return SqlAlchemyDocumentRepository(session)

# Отдаёт реализацию лога операций поверх Redis
def get_operation_log_repository(
        redis: Annotated[Redis, Depends(get_redis)],
) -> OperationLogRepository:
    return RedisOperationLogRepository(redis)

# Отдаёт реализацию PubSub поверх Redis Pub/Sub
def get_pubsub(
        redis: Annotated[Redis, Depends(get_redis)],
) -> PubSub:
    return RedisPubSub(redis)

def get_presence_store(
        redis: Annotated[Redis, Depends(get_redis)],
        settings: Annotated[Settings, Depends(get_settings)],
) -> RedisPresenceStore:
    return RedisPresenceStore(redis, ttl_seconds=settings.presence_heartbeat_ttl_seconds)


# ======================================================================================
# Слой 3: сервисы приложения. Получают на вход только интерфейсы
# ======================================================================================

def get_auth_service(
        user_repo: Annotated[UserRepository, Depends(get_user_repository)],
        settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(user_repo=user_repo, settings=settings)

def get_permission_service(
        document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
        permission_repo: Annotated[PermissionRepository, Depends(get_permission_repository)],
) -> PermissionService:
    return PermissionService(document_repo=document_repo, permission_repo=permission_repo)

def get_document_service(
        document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
        permission_service: Annotated[PermissionService, Depends(get_permission_service)],
) -> DocumentService:
    return DocumentService(document_repo=document_repo, permission_service=permission_service)


# Возвращает OT Controller — ядро OT поверх DocumentRepository и лога операций
def get_ot_controller(
        document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
        operation_log_repo: Annotated[OperationLogRepository, Depends(get_operation_log_repository)],
        settings: Annotated[Settings, Depends(get_settings)],
) -> OTController:
    return OTController(
        document_repo=document_repo,
        operation_log_repo=operation_log_repo,
        compact_threshold=settings.operation_log_compact_threshold,
    )

def get_collab_service(
        ot_controller: Annotated[OTController, Depends(get_ot_controller)],
        room_manager: Annotated[RoomManager, Depends(get_room_manager)],
        pubsub: Annotated[PubSub, Depends(get_pubsub)],
        presence_store: Annotated[RedisPresenceStore, Depends(get_presence_store)],
) -> CollabService:
    return CollabService(
        ot_controller=ot_controller,
        room_manager=room_manager,
        pubsub=pubsub,
        presence_store=presence_store,
    )

# Реестр доступных форматов экспорта
def get_exporters() -> dict[str, Exporter]:
    return {
        "txt": TxtExporter(),
        "docx": DocxExporter(),
    }

def get_export_service(
        document_service: Annotated[DocumentService, Depends(get_document_service)],
        exporters: Annotated[dict[str, Exporter], Depends(get_exporters)],
) -> ExportService:
    return ExportService(
        document_service=document_service, exporters=exporters,
    )