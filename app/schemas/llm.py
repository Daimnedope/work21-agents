from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatMessage(BaseModel):
    """Сообщение в чате"""
    role: str = Field(..., description="Роль: system, user, assistant")
    content: str = Field(..., description="Содержимое сообщения")


class ChatRequest(BaseModel):
    """Запрос на чат с LLM"""
    model: Optional[str] = Field(None, description="Модель LLM (опционально)")
    messages: List[ChatMessage] = Field(..., description="История сообщений")
    temperature: float = Field(0.0, ge=0, le=2, description="Температура генерации")
    max_tokens: int = Field(2000, ge=1, le=8000, description="Максимум токенов")


class ChatResponse(BaseModel):
    """Ответ от LLM"""
    model: str = Field(..., description="Использованная модель")
    response: str = Field(..., description="Ответ LLM")
    success: bool = Field(True, description="Успешность запроса")
    error: Optional[str] = Field(None, description="Сообщение об ошибке")


class SimpleChatRequest(BaseModel):
    """Простой запрос к LLM"""
    prompt: str = Field(..., description="Текст запроса")
    model: Optional[str] = Field(None, description="Модель (опционально)")


class SimpleChatResponse(BaseModel):
    """Простой ответ от LLM"""
    model: str = Field(..., description="Использованная модель")
    response: str = Field(..., description="Ответ LLM")
    success: bool = Field(True, description="Успешность запроса")


class EstimationRequest(BaseModel):
    """Запрос на оценку проекта"""
    title: str = Field(..., description="Название проекта")
    spec_text: str = Field(..., description="Техническое задание")


class TaskInfo(BaseModel):
    """Информация о задаче"""
    id: str
    title: str
    description: Optional[str] = None
    hours: int
    priority: str
    role: str
    depends_on: List[str] = []


class CostBreakdown(BaseModel):
    """Разбивка стоимости"""
    id: str
    title: str
    hours: int
    role: str
    rate: float
    cost: float


class CostEstimate(BaseModel):
    """Оценка стоимости"""
    breakdown: List[CostBreakdown]
    total: float


class TaskSchedule(BaseModel):
    """Расписание задачи"""
    id: str
    title: str
    role: str
    hours: int
    start_date: str
    end_date: str
    duration_days: int
    depends_on: List[str] = []


class TimelineEstimate(BaseModel):
    """Оценка сроков"""
    project_start: str
    project_end: str
    total_work_days: int
    role_days: Dict[str, int]
    task_schedule: List[TaskSchedule]


class ProjectInfo(BaseModel):
    """Информация о проекте"""
    title: str
    summary: str


class EstimationResponse(BaseModel):
    """Полный ответ с оценкой проекта"""
    project: ProjectInfo
    tasks: List[Dict[str, Any]]
    critical_paths: List[Any] = []
    cost_estimate: CostEstimate
    timeline_estimate: TimelineEstimate
    generated_at: str
    success: bool = True
    error: Optional[str] = None

