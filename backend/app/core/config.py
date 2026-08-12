from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE_PATH = Path(__file__).resolve().parents[3] / ".env"

# Все настройки приложения читаются из .env
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Приложение
    app_name: str = "gdocs-clone"
    debug: bool = False
    environment: str = "development" # development | staging | production

    # База данных
    postgres_db: str = ""
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # Redis
    redis_host: str = ""
    redis_port: int = 6379

    database_url: str = ""
    redis_url: str = ""

    db_pool_size: int = 10
    db_echo: bool = False # логировать ли каждый SQL-запрос

    # Auth / JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    guest_token_expire_hours: int = 24

    # CORS
    cors_allowed_origins: list[str] = []

    # OT / Collaboration

    """
    Порог сжатия лога операций. Когда количество операций превышает заданное
    значение, система объединяет старые правки с один snapshot.
    """
    operation_log_compact_threshold: int = 500

    """
    Время жизни (TTL) сигнала присутствия пользователя в секундах.
    Если от клиента не поступает "пульс", система считает, что пользователь
    отключилися и убирает его курсор из документа
    """
    presence_heartbeat_ttl_seconds: int = 30

    # Логирование
    log_level: str = "INFO"
    log_json: bool = True # True для прода (JSON-логи); False для читаемых логов в dev

    @model_validator(mode="after")
    def _build_connection_urls(self) -> "Settings":
        if not self.database_url:
            self.database_url = (f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}")
        if not self.redis_url:
            self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()