# Messenger API

Асинхронный API для мессенджера с поддержкой WebSocket для real-time сообщений.

## Технологии

- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- WebSocket
- JWT аутентификация
- Docker
- PDM (менеджер зависимостей)

## Функциональность

- Регистрация и аутентификация пользователей
- Создание личных и групповых чатов
- Отправка сообщений через REST API и WebSocket
- Отслеживание статуса прочтения сообщений
- Real-time уведомления о новых сообщениях
- История сообщений с пагинацией

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/endlessmeal/test_case_mango.git
cd test_case_mango
```

2. Создайте файл `.env` в директории `app` на основе `.env.example`:
```bash
cp app/.env.example app/.env
```

3. Запустите проект с помощью Docker Compose:
```bash
docker-compose up --build
```

API будет доступно по адресу: http://localhost:8080

## API Endpoints

### Пользователи
- `POST /api/v1/users` - Создание нового пользователя
- `GET /api/v1/users` - Получение списка пользователей (с пагинацией)
- `GET /api/v1/users/{user_id}` - Получение информации о пользователе
- `PUT /api/v1/users/{user_id}` - Обновление данных пользователя
- `DELETE /api/v1/users/{user_id}` - Удаление пользователя

### Аутентификация
- `POST /api/v1/users/login` - Вход в систему
- `POST /api/v1/users/refresh` - Обновление токена

### Чаты
- `GET /api/v1/chats` - Получение списка чатов пользователя
- `POST /api/v1/chats` - Создание нового чата
- `GET /api/v1/chats/{chat_id}` - Получение информации о чате
- `GET /api/v1/chats/{chat_id}/messages` - Получение сообщений чата
- `POST /api/v1/chats/{chat_id}/participants` - Добавление участника в чат
- `DELETE /api/v1/chats/{chat_id}/participants/{user_id}` - Удаление участника из чата

### WebSocket
- `ws://localhost:8080/ws/{chat_id}?token=access_token` - WebSocket подключение для real-time сообщений
  - Отправка сообщений: `{"type": "message", "text": "Текст сообщения"}`
  - Отметка о прочтении: `{"type": "read", "message_id": "uuid"}`

## Структура проекта

```
app/
├── alembic/          # Миграции базы данных
├── core/             # Основные настройки приложения
├── endpoints/        # API endpoints
├── models/           # SQLAlchemy модели
├── repositories/     # Репозитории для работы с БД
├── schemas/          # Pydantic схемы
└── services/         # Бизнес-логика
```

## Разработка

1. Установите зависимости:
```bash
pdm install
```

2. Создайте виртуальное окружение:
```bash
pdm venv create
```

3. Активируйте виртуальное окружение:
```bash
pdm venv activate
```

4. Запустите миграции:
```bash
alembic upgrade head
```

5. Запустите сервер разработки:
```bash
uvicorn app.main:app --reload
```

## Тестирование

```bash
pdm run pytest
```

## Лицензия

MIT 