# CLAUDE.md - Work21 AI Agent

## Обзор проекта

**Work21 AI Agent** — микросервис для оценки проектов с использованием GigaChat (Сбер). Анализирует техническое задание и генерирует:
- Список задач с оценкой времени
- Расчёт стоимости по ролям
- Timeline проекта

## Технологический стек

- **Framework:** FastAPI (Python 3.11+)
- **LLM:** GigaChat (langchain-gigachat)
- **Validation:** Pydantic v2
- **Container:** Docker

## Структура проекта

```
work21-agents/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── api/
│   │   └── llm.py           # LLM endpoints
│   ├── services/
│   │   └── gigachat_service.py  # GigaChat интеграция
│   └── core/
│       └── config.py        # Настройки
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Ключевые команды

```bash
# Запуск с Docker
docker compose up -d

# Локальный запуск
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Проверка здоровья
curl http://localhost:8080/api/v1/llm/health
```

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/llm/health` | Проверка здоровья |
| POST | `/api/v1/llm/chat` | Чат с LLM |
| POST | `/api/v1/llm/estimate` | Полная оценка проекта |

### POST /api/v1/llm/estimate

**Request:**
```json
{
  "title": "Название проекта",
  "spec_text": "Описание технического задания..."
}
```

**Response:**
```json
{
  "project": {
    "title": "Название",
    "summary": "Краткое описание"
  },
  "tasks": [
    {
      "id": "task-1",
      "title": "Задача",
      "hours": 8,
      "priority": "high",
      "role": "backend"
    }
  ],
  "cost_estimate": {
    "total": 150000,
    "breakdown": [...]
  },
  "timeline_estimate": {
    "total_work_days": 15,
    "project_start": "2024-01-15",
    "project_end": "2024-02-05"
  },
  "success": true
}
```

## Переменные окружения

```env
# Обязательно
GIGACHAT_CREDENTIALS=ваш_base64_ключ_gigachat

# Опционально
GIGACHAT_MODEL=GigaChat-Pro
GIGACHAT_SCOPE=GIGACHAT_API_PERS
SERVER_PORT=8080
LLM_PROVIDER=gigachat
```

## Получение GigaChat API ключа

1. Зарегистрируйтесь на https://developers.sber.ru
2. Создайте проект и получите Client ID + Client Secret
3. Закодируйте в base64: `echo -n "client_id:client_secret" | base64`
4. Используйте результат как `GIGACHAT_CREDENTIALS`

## Роли и ставки

Агент использует следующие роли для расчёта стоимости:

| Роль | Ставка (₽/час) |
|------|----------------|
| backend | 2000 |
| frontend | 1800 |
| devops | 2200 |
| qa | 1500 |
| ux | 1600 |
| pm | 2000 |

## Swagger UI

Документация доступна по адресу: `/swagger-ui.html`

## Связанные сервисы

- **Backend:** https://github.com/oinuritto/work21-backend
- **Frontend:** https://github.com/ChargeOnTop/work21-fr
- **Admin Panel:** https://github.com/Daimnedope/work21-admins
- **Deploy:** https://github.com/ChargeOnTop/work21-deploy

## Production

- **URL:** https://api.work-21.com/agent
- **Health:** https://api.work-21.com/agent/api/v1/llm/health

