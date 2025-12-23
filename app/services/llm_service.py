"""
Сервис для работы с GigaChat LLM
"""
import logging
from typing import List, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class GigaChatProvider:
    """Провайдер для GigaChat (Сбер)"""
    
    def __init__(self):
        self.api_key = settings.GIGACHAT_API_KEY
        self.scope = settings.GIGACHAT_SCOPE
        self.model = settings.GIGACHAT_MODEL
        self._chat_model = None
    
    def _get_model(self):
        if self._chat_model is None:
            try:
                from langchain_gigachat.chat_models import GigaChat
                self._chat_model = GigaChat(
                    credentials=self.api_key,
                    scope=self.scope,
                    model=self.model,
                    verify_ssl_certs=False,
                )
            except ImportError:
                raise ImportError("langchain-gigachat не установлен")
        return self._chat_model
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000
    ) -> str:
        llm = self._get_model()
        response = llm.invoke(messages)
        
        # Извлекаем текст из ответа
        if hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'text'):
            return response.text
        else:
            return str(response)
    
    def get_model_name(self) -> str:
        return self.model


class LLMService:
    """Сервис для работы с GigaChat LLM"""
    
    def __init__(self):
        self._provider: Optional[GigaChatProvider] = None
    
    def _get_provider(self) -> GigaChatProvider:
        if self._provider is None:
            self._provider = GigaChatProvider()
        return self._provider
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000
    ) -> str:
        """Отправить сообщение в чат GigaChat"""
        provider = self._get_provider()
        return await provider.chat(messages, model, temperature, max_tokens)
    
    async def ask(self, prompt: str, model: Optional[str] = None) -> str:
        """Простой запрос к GigaChat"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model)
    
    def get_model_name(self) -> str:
        """Получить название модели"""
        return self._get_provider().get_model_name()


# Синглтон сервиса
llm_service = LLMService()
