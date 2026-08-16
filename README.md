# Google Docs Clone

Учебный pet-проект — совместный текстовый редактор в духе Google Docs. Бэкенд на FastAPI реализует
многопользовательское редактирование документов в реальном времени по алгоритму
**Operational Transformation (OT)** поверх WebSocket, с REST API для аутентификации, CRUD над документами,
правами доступа и экспортом в файлы. Фронтенд — заготовка на React + Vite (пока не реализован).

## Стек технологий

**Backend**
- Python 3.13, FastAPI, Uvicorn
- SQLAlchemy 2.0 (async) + PostgreSQL 18, Alembic (миграции)
- Redis 8 — pub/sub между инстансами, presence (кто сейчас в документе) и лог операций
- JWT (PyJWT) + Argon2 (passlib) — аутентификация, включая гостевой вход
- structlog — структурированное логирование
- python-docx — экспорт документов в `.docx`
- pytest / pytest-asyncio / hypothesis / httpx — тесты (unit, integration, property-based)

**Frontend**
- React 19, TypeScript, Vite 8 (сейчас содержит только стартовый шаблон Vite, UI редактора не реализован)

**Инфраструктура**
- Docker / docker-compose (сервисы: `backend`, `frontend`, `postgres`, `redis`)

## Архитектура

Backend построен по принципам чистой архитектуры (Clean/Hexagonal Architecture) с чётким разделением слоёв:

```
backend/app/
├── api/                 # Транспортный слой: REST (v1) и WebSocket роуты, схемы запросов/ответов
│   ├── v1/               # /api/v1/auth, /api/v1/documents — REST эндпоинты
│   └── ws/               # /ws/documents/{document_id} — WebSocket-комната документа
├── application/         # Слой use-case'ов
│   ├── services/          # AuthService, DocumentService, PermissionService, ExportService
│   ├── collab/            # CollabService, RoomManager — оркестрация совместного редактирования
│   ├── ot/                # Контроллер операций (применение/трансформация на лету)
│   └── interfaces/        # Абстракции (Exporter, PubSub) для инверсии зависимостей
├── domain/              # Ядро предметной области, не зависящее от фреймворков
│   ├── entities/           # User, Document, Permission (Role: VIEWER/EDITOR/OWNER)
│   ├── ot/                 # Чистая логика OT: Operation (Retain/Insert/Delete), apply, transform
│   ├── repositories/       # Абстрактные интерфейсы репозиториев
│   └── exceptions.py       # Доменные исключения
├── infrastructure/      # Реализации интерфейсов домена
│   ├── db/                 # SQLAlchemy-модели и репозитории (Postgres)
│   ├── redis/               # Клиент Redis: pub/sub, лог операций, presence-store
│   └── export/              # Экспортёры в .txt и .docx
├── mappers/             # Преобразование между доменными сущностями и DTO/ORM-моделями
├── core/                # Конфигурация (Settings), DI-контейнер, security (JWT), логирование
└── main.py              # Точка входа FastAPI-приложения
```

### Совместное редактирование (OT)

Каждый документ хранится как снапшот текста (`content_snapshot`) в Postgres плюс лог операций в Redis.
Клиенты подключаются к WebSocket-комнате `/ws/documents/{document_id}` и обмениваются операциями вида
`Retain / Insert / Delete`. При конфликте ревизий сервер трансформирует операции (`transform`) относительно
уже применённых, чтобы все клиенты сошлись к одному состоянию документа. `RoomManager` держит активные
комнаты и рассылает изменения подписанным соединениям через Redis pub/sub (что позволяет масштабировать
бэкенд на несколько инстансов), а presence-store в Redis с TTL отслеживает, кто сейчас находится в документе
(heartbeat каждые 15 секунд, TTL настраивается).

## Основные возможности

- Регистрация/логин по email+паролю, гостевой вход без регистрации с последующим апгрейдом до полноценного
  аккаунта, refresh-токены
- CRUD над документами (создание, список, получение, переименование, мягкое удаление)
- Ролевая модель доступа к документу: `VIEWER` / `EDITOR` / `OWNER`
- Совместное редактирование в реальном времени через WebSocket с разрешением конфликтов (OT)
- Presence — отображение активных участников документа
- Экспорт документа в `.txt` и `.docx`

## API

### REST (`/api/v1`)

**Auth** (`/api/v1/auth`)
| Метод | Путь | Описание |
|---|---|---|
| POST | `/register` | Регистрация нового пользователя |
| POST | `/login` | Вход по email/паролю |
| POST | `/guest` | Гостевой вход без регистрации |
| POST | `/upgrade` | Превращение гостя в полноценного пользователя |
| POST | `/refresh` | Обновление пары токенов |

**Documents** (`/api/v1/documents`)
| Метод | Путь | Описание |
|---|---|---|
| POST | `/` | Создать документ |
| GET | `/` | Список своих документов (пагинация `limit`/`offset`) |
| GET | `/{document_id}` | Получить документ (содержимое + ревизия) |
| PATCH | `/{document_id}` | Переименовать документ |
| DELETE | `/{document_id}` | Удалить документ (мягкое удаление) |
| GET | `/{document_id}/export?format=txt\|docx` | Экспортировать документ в файл |

### WebSocket

| Путь | Описание |
|---|---|
| `/ws/documents/{document_id}?token=...` | Комната совместного редактирования документа. После подключения сервер присылает `sync` (текущее содержимое и ревизию); клиент отправляет операции (`op`) и heartbeat-сообщения, сервер отвечает `ack` или `error` |

Аутентификация в WebSocket — через access- или guest-токен, переданный query-параметром `token`.

### Прочее

- `GET /health` — health-check приложения

## Переменные окружения

Конфигурация читается из `.env` в корне проекта (см. `.env.example`):

```
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379

JWT_SECRET_KEY=
```

Прочие настройки (алгоритм и время жизни JWT, TTL presence, порог сжатия лога операций, CORS,
уровень логирования и т.д.) имеют значения по умолчанию в `backend/app/core/config.py` и при
необходимости также переопределяются через `.env`.

## Запуск

```commandline
docker compose up --build
```

После запуска:
- backend (FastAPI): `http://localhost:8000`
- frontend (Vite dev-server): `http://localhost:5173`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Миграции базы данных выполняются через Alembic (`backend/alembic`).

## Тесты

Тесты бэкенда лежат в `backend/tests` и делятся на:
- `tests/unit` — юнит-тесты доменной логики OT (`apply`, `transform`, в т.ч. property-based тесты на
  `hypothesis`) и сервисов уровня application (с фейковыми репозиториями)
- `tests/integration` — интеграционные тесты REST API (`auth`, `documents`)

Запуск (из директории `backend`, в виртуальном окружении с установленными зависимостями из
`requirements.txt`):

```commandline
pytest
```

## Контакты

- **Автор:** Михаил Шубин
- **Email:** <mishaelshubin@gmail.com>
- **GitHub:** [mikhailshubin26](https://github.com)
- **Твиттер:** [@mikleshubin](https://x.com)

