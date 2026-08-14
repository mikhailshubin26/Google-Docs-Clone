from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger, configure_logging
from app.domain.exceptions import DomainError

from app.api.v1.router import router as v1_router
from app.api.ws.router import router as ws_router

settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)

# Место для инициализации/освобождения ресурсов на весь процесс
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app starting", environemt=settings.environemt)
    yield
    logger.info("app stopping")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,

    # Разрешённые источники (домены), с которых frontend может обращаться к API
    allow_origins=settings.cors_allowed_origins,

    # Разрешает отправку coockie и других credentials
    allow_credentials=True,

    # Разрешает HTTP-методы: GET, POST, DELETE, PUT и т.д.
    allow_methods=["*"],

    # Разраешает любые HTTP-заголовки в запросах
    allow_headers=["*"],
)

# Обработчик доменных исключений, не пойманных в конкретном роуте
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    logger.warning("unhandled_domain_error", error_type=type(exc).__name__, detail=str(exc))
    return JSONResponse(status_code=400 , content={"detail": str(exc)})

@app.get("/health")
async def health_check() -> dict[str, str]
    return {"status": "ok"}

app.include_router(v1_router)
app.include_router(ws_router)