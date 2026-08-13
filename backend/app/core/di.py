from typing import Annotated

from redis.asyncio import Redis
from fastapi import Depends
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
from app.infrastructure.redis.operation_log import RedisOperationLogRepository
from app.application.services.auth_service import AuthService
from app.application.services.permission_service import PermissionService
from app.application.services.document_service import DocumentService

# ======================================================================================
# Слой 1: низкоуровневые ресурсы (engine БД, Redis-клиент); Создаются один раз на процесс
# ======================================================================================

_engine = None
_session_factory = None
_redis_client: Redis | None = None

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
        permission_service: Annotated[PermissionService, Depends(get_permission_services)],
) -> DocumentService:
    return DocumentService(document_repo=document_repo, permission_service=permission_service)