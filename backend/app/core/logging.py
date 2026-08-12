import sys

import logging
import structlog

from app.core.config import Settings

def configure_logging(settings: Settings) -> None:
    # Базовая настройка logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level,
    )

    # Обработчики, которые добавляются к каждой записи лога перед выводом
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Если prod — JSON, если dev — консольный вывод
    renderer: structlog.types.Processor = (structlog.processors.JSONRenderer() if settings.log_json else structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level),
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Функция возвращает именнованный логгер
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)