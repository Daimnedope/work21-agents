"""
Agent Estimator Service - Python FastAPI версия
AI-агент для оценки проектов на базе GigaChat
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import llm_router

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения"""
    logger.info(f"🚀 Agent Estimator Service запускается...")
    logger.info(f"   LLM: GigaChat ({settings.GIGACHAT_MODEL})")
    yield
    logger.info("👋 Agent Estimator Service останавливается...")


# Создаём приложение
app = FastAPI(
    title="Agent Estimator Service API",
    description="""
    Микросервис AI-аналитика для оценки проектов на базе GigaChat.
    
    ## Возможности
    
    * **Простые запросы** — отправка промптов к GigaChat
    * **Чат с историей** — контекстные диалоги с моделью  
    * **Оценка проектов** — анализ ТЗ, генерация задач, расчёт стоимости и сроков
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/swagger-ui.html",
    redoc_url="/redoc",
    openapi_url="/api-docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(llm_router)


@app.get("/", tags=["Root"])
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Agent Estimator Service",
        "version": "2.0.0",
        "language": "Python",
        "framework": "FastAPI",
        "llm": "GigaChat",
        "docs": "/swagger-ui.html",
        "health": "/api/v1/llm/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "UP", "llm": "GigaChat"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVER_PORT,
        reload=settings.DEBUG
    )
