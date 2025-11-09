# FastAPI Project - Система управления задачами и командами

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-100000?style=for-the-badge&logo=sqlalchemy&logoColor=white)

Производственная система для управления задачами, командами, встречами и оценками сотрудников с ролевой моделью доступа.

## Возможности

### Аутентификация и авторизация
- JWT-аутентификация через `fastapi-users`
- Ролевая модель: пользователь, менеджер, администратор команды, суперадмин
- Регистрация, верификация, сброс пароля

### Управление командами
- Создание и управление командами
- Система приглашений с инвайт-кодами
- Назначение администраторов команд

### Управление задачами
- Создание, назначение и отслеживание задач
- Статусы задач: открыта, в процессе, завершена
- Комментарии к задачам
- Назначение исполнителей и проверяющих

### Календарь и встречи
- Личный календарь с задачами и встречами
- Планирование встреч с участниками
- Проверка конфликтов расписания
- Просмотр по дням, месяцам, предстоящие события

### Система оценок
- Оценка завершенных задач (1-5 баллов)
- Расчет среднего рейтинга сотрудников
- Защита от дублирования оценок

### Админ-панель
- Полнофункциональная админка на SQLAdmin
- Управление всеми сущностями системы
- Визуализация связей между моделями

## Архитектура

Проект построен с соблюдением лучших практик и паттернов проектирования:

### Структура проекта

```bash
.
├── app/
│   ├── admin.py              # Админ-панель SQLAdmin
│   ├── database/
│   │   ├── database.py       # Конфигурация БД
│   │   ├── models.py         # SQLAlchemy модели
│   │   ├── repository.py     # Паттерн Repository
│   │   └── __init__.py
│   ├── dependencies.py       # Зависимости и проверки прав
│   ├── routers/              # API роутеры
│   │   ├── calendar.py       # Календарь и события
│   │   ├── evaluations.py    # Система оценок
│   │   ├── meetings.py       # Управление встречами
│   │   ├── tasks.py          # Управление задачами
│   │   ├── teams.py          # Управление командами
│   │   └── users.py          # Пользователи и профиль
│   ├── schemas.py            # Pydantic схемы
│   └── users.py              # FastAPI-users конфигурация
├── main.py                   # Точка входа приложения
└── requirements.txt          # Зависимости
```

### Используемые паттерны
- **Repository Pattern** - абстракция доступа к данным
- **Dependency Injection** - через FastAPI Depends
- **Factory Pattern** - создание стратегий аутентификации
- **Layered Architecture** - четкое разделение ответственности

## Технологический стек

- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL + asyncpg
- **ORM**: SQLAlchemy 2.0+ (асинхронный)
- **Authentication**: FastAPI-Users + JWT
- **Admin Panel**: SQLAdmin
- **Validation**: Pydantic v2
- **Environment**: python-dotenv

## Установка и запуск

### 1. Клонирование и настройка
```bash
git clone <your-repo-url>
cd FastAPI_project
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
# или
.venv\Scripts\activate     # Windows
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка окружения
Создайте файл `.env` в корне проекта:
```env
# Database
DB_NAME=name
DB_HOST=host
DB_PORT=port
DB_USER=user
DB_PASS=password

# Security
SECRET_KEY=key

# Admin
ADMIN_EMAIL=admin@email
ADMIN_PASSWORD=admin password
ADMIN_USERNAME=admin username
```

### 4. Запуск приложения
```bash
python main.py
```

Приложение будет доступно по адресу: http://localhost:8000

## API Документация

После запуска доступны:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Admin Panel**: http://localhost:8000/admin

## Ролевая модель

### Роли и права доступа

| Роль | Описание | Права |
|------|-----------|--------|
| **user** | Обычный пользователь | Собственные задачи, календарь |
| **manager** | Менеджер | + Создание задач, просмотр команды |
| **team_admin** | Админ команды | + Управление командой, встречами |
| **admin** | Суперадмин | Полный доступ ко всем функциям |

## Модели данных

### Основные сущности:
- **User** - пользователи системы
- **Team** - рабочие команды  
- **Task** - задачи с исполнителями и статусами
- **Meeting** - встречи с участниками
- **Evaluation** - оценки выполненных задач
- **Comment** - комментарии к задачам

## Основные workflow

### 1. Создание команды и приглашение участников
```
Админ команды → Создает команду → Генерирует инвайт-код → Участники вступают по коду
```

### 2. Рабочий процесс задачи
```
Менеджер создает задачу → Назначает исполнителя → 
Исполнитель работает → Меняет статус → 
Проверяющий оценивает → Система считает рейтинг
```

### 3. Планирование встреч
```
Организатор создает встречу → Добавляет участников → 
Система проверяет конфликты → Участники видят в календаре
```

## Примеры использования API

### Аутентификация
```bash
# Регистрация
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "string", "username": "john"}'

# Логин
curl -X POST "http://localhost:8000/auth/jwt/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "string"}'
```

### Работа с задачами
```bash
# Создание задачи (требуются права менеджера)
curl -X POST "http://localhost:8000/tasks/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_name": "Новая задача", "task_description": "Описание"}'

# Получение своих задач
curl -X GET "http://localhost:8000/tasks/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Ключевые особенности реализации

### Чистая архитектура
- Разделение на слои: роутеры → репозитории → модели
- Использование Pydantic схем для валидации
- Dependency Injection для управления зависимостями

### Безопасность
- JWT токены с временем жизни
- Проверка прав доступа на уровне эндпоинтов
- Защита от SQL-инъекций через SQLAlchemy

### Производительность
- Асинхронные запросы к базе данных
- Оптимизированные SQL-запросы через репозитории
- Пагинация для больших наборов данных
