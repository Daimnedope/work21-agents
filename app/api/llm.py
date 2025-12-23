"""
API эндпоинты для работы с LLM
"""
from fastapi import APIRouter, HTTPException
import logging

from app.schemas import (
    ChatRequest,
    ChatResponse,
    SimpleChatRequest,
    SimpleChatResponse,
    EstimationRequest,
    EstimationResponse,
)
from app.services.llm_service import llm_service
from app.services.analyst_service import analyst_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/llm", tags=["LLM API"])


@router.post("/ask", response_model=SimpleChatResponse, summary="Простой запрос к LLM")
async def ask(request: SimpleChatRequest):
    """
    Простой запрос к LLM.
    Отправляет промпт и получает ответ.
    """
    try:
        response = await llm_service.ask(request.prompt, request.model)
        return SimpleChatResponse(
            model=llm_service.get_model_name(),
            response=response,
            success=True
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе к LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse, summary="Отправить сообщение в чат")
async def chat(request: ChatRequest):
    """
    Отправить сообщение в чат с историей.
    Поддерживает системные сообщения и контекст.
    """
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        response = await llm_service.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return ChatResponse(
            model=llm_service.get_model_name(),
            response=response,
            success=True
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе к LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate", response_model=EstimationResponse, summary="Оценка проекта")
async def estimate_project(request: EstimationRequest):
    """
    AI-аналитик: полная оценка проекта.
    
    Анализирует техническое задание и возвращает:
    - Список задач с оценкой времени
    - Стоимость проекта по ролям
    - Сроки выполнения с учётом зависимостей
    """
    try:
        result = await analyst_service.analyze_project(
            title=request.title,
            spec_text=request.spec_text
        )
        return EstimationResponse(
            project=result["project"],
            tasks=result["tasks"],
            critical_paths=result.get("critical_paths", []),
            cost_estimate=result["cost_estimate"],
            timeline_estimate=result["timeline_estimate"],
            generated_at=result["generated_at"],
            success=True
        )
    except ValueError as e:
        logger.error(f"Ошибка валидации: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при оценке проекта: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Проверка здоровья сервиса")
async def health():
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy",
        "provider": llm_service._get_provider().__class__.__name__,
        "model": llm_service.get_model_name()
    }

