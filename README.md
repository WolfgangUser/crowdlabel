# CrowdLabel — Платформа краудсорсинговой разметки данных для ML

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com)
[![12-Factor](https://img.shields.io/badge/12--Factor-App-orange)](https://12factor.net)

Курсовой проект по дисциплине «Веб-технологии» (МИРЭА, СМКО 7.5.1/04.И.05-18).

---

## Содержание

1. [Описание проекта](#описание-проекта)
2. [Архитектура](#архитектура)
3. [Стек технологий](#стек-технологий)
4. [Структура проекта](#структура-проекта)
5. [Быстрый старт](#быстрый-старт)
6. [API документация](#api-документация)
7. [Ролевая модель](#ролевая-модель)
8. [Тестирование](#тестирование)
9. [Развёртывание](#развёртывание)
10. [12-факторная методология](#12-факторная-методология)

---

## Описание проекта

**CrowdLabel** — веб-платформа для организации краудсорсинговой разметки датасетов, используемых при обучении моделей машинного обучения. Позволяет:

- Создавать задачи разметки (классификация изображений, NER, сентимент-анализ и др.)
- Привлекать разметчиков (аннотаторов) через публичный интерфейс
- Контролировать качество разметки через систему верификации
- Экспортировать размеченные данные в форматах JSONL, CSV, COCO

---

## Архитектура

Трёхуровневая клиент-серверная архитектура (3-tier):

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT TIER                       │
│          React 18 SPA (Vite + TypeScript)           │
│    Zustand · React Query · React Router v6          │
└───────────────────┬─────────────────────────────────┘
                    │ HTTPS / REST JSON
┌───────────────────▼─────────────────────────────────┐
│                 APPLICATION TIER                    │
│        FastAPI 0.111 (Python 3.11, Uvicorn)        │
│   JWT Auth · Pydantic v2 · SQLAlchemy 2.0 async    │
│              Alembic · Celery + Redis               │
└───────────────────┬─────────────────────────────────┘
                    │ asyncpg / SQLAlchemy
┌───────────────────▼─────────────────────────────────┐
│                   DATA TIER                         │
│     PostgreSQL 16          Redis 7 (cache/queue)    │
│     (primary store)        MinIO (object storage)   │
└─────────────────────────────────────────────────────┘
```

Подробные UML-диаграммы: [`docs/uml/`](docs/uml/)

---

## Стек технологий

| Слой | Технология | Обоснование |
|------|-----------|-------------|
| **Backend** | Python 3.11 + FastAPI | Async-first, автодокументация OpenAPI, высокая производительность |
| **ORM** | SQLAlchemy 2.0 async | Type-safe, поддержка async, миграции через Alembic |
| **База данных** | PostgreSQL 16 | ACID, JSON-поля, полнотекстовый поиск |
| **Кэш / очередь** | Redis 7 | Session store, Celery broker |
| **Фоновые задачи** | Celery 5 | Экспорт датасетов, уведомления |
| **Авторизация** | JWT (python-jose) + bcrypt | Stateless, масштабируемо |
| **Frontend** | React 18 + TypeScript + Vite | SPA, type safety, быстрая сборка |
| **State** | Zustand + React Query | Минималистичный глобальный стейт + серверный кэш |
| **UI** | Tailwind CSS 3 | Utility-first, консистентный дизайн |
| **Контейнеры** | Docker + Docker Compose | Воспроизводимая среда, 12-factor |
| **CI/CD** | GitHub Actions | Автотесты, линтинг, сборка образов |

---

## Структура проекта

```
crowdlabel/
├── backend/                    # FastAPI приложение
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/  # Роутеры (auth, tasks, annotations, users, datasets)
│   │   ├── core/               # Конфигурация, безопасность, зависимости
│   │   ├── db/                 # Сессии БД, base model
│   │   ├── models/             # SQLAlchemy ORM модели
│   │   ├── schemas/            # Pydantic v2 схемы запросов/ответов
│   │   ├── services/           # Бизнес-логика
│   │   └── utils/              # Хелперы, экспорт, pagination
│   ├── tests/
│   │   ├── fuzz/               # Фаззинг-тесты (Atheris / hypothesis)
│   │   ├── test_auth.py
│   │   ├── test_tasks.py
│   │   └── test_roles.py
│   ├── alembic/                # Миграции БД
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py                 # Тестовые данные
│
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── api/                # Axios клиенты
│   │   ├── components/         # UI компоненты
│   │   ├── pages/              # Страницы (Login, Dashboard, Tasks, Admin)
│   │   ├── store/              # Zustand stores
│   │   └── types/              # TypeScript типы
│   ├── Dockerfile
│   └── vite.config.ts
│
├── docs/
│   ├── uml/                    # PlantUML диаграммы
│   └── api/                    # OpenAPI spec
│
├── docker-compose.yml          # Оркестрация сервисов
├── docker-compose.prod.yml     # Продакшн конфигурация
├── .env.example                # Пример переменных окружения
├── Makefile                    # Команды разработки
└── README.md
```

---

## Быстрый старт

### Предварительные требования

- Docker 24+ и Docker Compose v2
- Git

### Локальная разработка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-org/crowdlabel.git
cd crowdlabel

# 2. Скопировать и заполнить .env
cp .env.example .env

# 3. Запустить все сервисы
docker compose up -d

# 4. Применить миграции и заполнить БД тестовыми данными
docker compose exec backend alembic upgrade head
docker compose exec backend python seed.py

# 5. Открыть приложение
# Frontend:  http://localhost:5173
# API docs:  http://localhost:8000/docs
# Adminer:   http://localhost:8080
```

### Тестовые аккаунты

| Роль | Email | Пароль |
|------|-------|--------|
| Admin | admin@crowdlabel.io | Admin123! |
| Manager | manager@crowdlabel.io | Manager123! |
| Annotator | annotator@crowdlabel.io | Annotator123! |

---

## API документация

Автогенерируемая документация доступна после запуска:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Основные эндпоинты

```
POST   /api/v1/auth/register       Регистрация
POST   /api/v1/auth/login          Вход (JWT)
POST   /api/v1/auth/refresh        Обновление токена

GET    /api/v1/tasks               Список задач разметки
POST   /api/v1/tasks               Создать задачу [manager+]
GET    /api/v1/tasks/{id}          Получить задачу
PUT    /api/v1/tasks/{id}          Обновить задачу [manager+]
DELETE /api/v1/tasks/{id}          Удалить задачу [admin]

POST   /api/v1/annotations         Отправить разметку [annotator+]
GET    /api/v1/annotations/{task}  Разметки задачи [manager+]
PUT    /api/v1/annotations/{id}/verify  Верифицировать [manager+]

GET    /api/v1/datasets            Список датасетов
POST   /api/v1/datasets/{id}/export  Экспортировать [manager+]

GET    /api/v1/users               Список пользователей [admin]
PUT    /api/v1/users/{id}/role     Изменить роль [admin]
```

---

## Ролевая модель

```
ADMIN
 ├── Полный доступ ко всем ресурсам
 ├── Управление пользователями и ролями
 └── Системные настройки

MANAGER
 ├── Создание / редактирование задач и датасетов
 ├── Верификация разметки
 └── Просмотр аналитики

ANNOTATOR (по умолчанию)
 ├── Просмотр доступных задач
 ├── Отправка разметки
 └── Просмотр своей статистики
```

Попытки выполнить действия без необходимой роли возвращают `403 Forbidden`.

---

## Тестирование

```bash
# Модульные и интеграционные тесты
docker compose exec backend pytest tests/ -v --cov=app

# Фаззинг-тестирование (Hypothesis)
docker compose exec backend pytest tests/fuzz/ -v

# Тесты ролевой модели
docker compose exec backend pytest tests/test_roles.py -v
```

---

## Развёртывание

### Docker (продакшн)

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Облачное развёртывание (Railway / Render / VPS)

Подробная инструкция: [`docs/deployment.md`](docs/deployment.md)

---

## 12-факторная методология

| Фактор | Реализация |
|--------|-----------|
| **I. Кодовая база** | Один Git-репозиторий, ветки `main`/`develop` |
| **II. Зависимости** | `requirements.txt` + `package.json`, изолированы в Docker |
| **III. Конфигурация** | `.env` файлы, `pydantic-settings`, никаких секретов в коде |
| **IV. Сторонние сервисы** | PostgreSQL, Redis, MinIO подключаются через URL из env |
| **V. Сборка/релиз/запуск** | GitHub Actions: build → test → push image → deploy |
| **VI. Процессы** | Stateless FastAPI воркеры, состояние в БД/Redis |
| **VII. Привязка портов** | Uvicorn слушает `0.0.0.0:8000`, проброс через Compose |
| **VIII. Параллелизм** | Несколько воркеров Uvicorn + Celery workers |
| **IX. Утилизируемость** | Graceful shutdown, быстрый старт контейнеров |
| **X. Паритет сред** | Docker Compose одинаков для dev/staging/prod |
| **XI. Логи** | Структурированные JSON-логи в stdout (loguru) |
| **XII. Задачи администрирования** | `seed.py`, Alembic — отдельные одноразовые процессы |
