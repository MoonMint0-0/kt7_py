# TaskTrackerAPI

Backend-сервис трекера задач на **FastAPI** с модульной архитектурой, PostgreSQL, миграциями Alembic, JWT-аутентификацией, ролевой моделью (RBAC), rate limiting, фоновыми задачами на Celery + Redis и автотестами.

## Стек технологий

* **Python 3.12+** / **FastAPI**
* **PostgreSQL 16** + **SQLAlchemy 2.0** + **Alembic**
* **JWT** (`python-jose`, `passlib[bcrypt]`) + **RBAC** (`user`, `admin`) + **SlowAPI** (rate limiting)
* **Celery** + **Redis 7** (фоновые задачи)
* **Docker** & **Docker Compose**
* **Pytest** + **GitHub Actions** (CI)

## Структура проекта

```text
├── alembic/                 # Миграции базы данных
├── app/
│   ├── core/                # Конфигурация, подключение к БД, безопасность и JWT
│   ├── modules/
│   │   ├── users/           # Регистрация, вход, профиль, управление ролями (RBAC)
│   │   ├── projects/        # CRUD-операции для проектов
│   │   └── tasks/           # CRUD-операции для задач + постановка задач в Celery
│   ├── tasks_worker/        # Настройка Celery и фоновые задачи
│   └── main.py              # Точка входа FastAPI, middleware (CORS, RateLimit)
├── tests/                   # Автотесты API (pytest)
├── .github/workflows/ci.yml # CI-пайплайн GitHub Actions
├── Dockerfile
└── docker-compose.yml
