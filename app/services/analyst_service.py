"""
Сервис AI-аналитика для оценки проектов.
Анализирует ТЗ, создаёт задачи, оценивает стоимость и сроки.
"""
import re
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


# Ставки по ролям (рублей/час)
DEFAULT_RATES_PER_HOUR = {
    "backend": 500,
    "frontend": 350,
    "devops": 600,
    "qa": 300,
    "ux": 600,
    "pm": 800,
    "default": 500
}


def _clean_text(s: str) -> str:
    """Очистка текста от лишних пробелов"""
    return re.sub(r'\s+', ' ', s).strip()


def _format_date(dt: datetime) -> str:
    """Форматирование даты"""
    return dt.strftime("%d.%m.%Y")


def _extract_json_block(text: str) -> Optional[str]:
    """
    Извлекает JSON блок из текста.
    Поддерживает ```json ... ``` и просто { ... }
    """
    # Сначала ищем ```json``` блок
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if m:
        return m.group(1)

    # Ищем первый { ... } блок
    start = text.find("{")
    if start == -1:
        return None
    
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None


class AnalystService:
    """Сервис AI-аналитика для оценки проектов"""
    
    async def generate_tasks_from_spec(
        self, 
        title: str, 
        spec_text: str
    ) -> Dict[str, Any]:
        """
        Генерирует структурированный список задач из ТЗ.
        Возвращает JSON с проектом, задачами и критическими путями.
        """
        title = _clean_text(title)
        spec_text = _clean_text(spec_text)

        prompt = f"""
Ты — профессиональный проект-аналитик. Преобразуй техническое задание в строгий формат JSON для планирования проекта.

Шаблон ответа (обязательный):
{{
  "project": {{
    "title": "<Название проекта>",
    "summary": "<Краткое описание проекта>"
  }},
  "tasks": [
    {{
      "id": "T1",
      "title": "Название задачи",
      "description": "Описание для исполнителя, 1-2 предложения.",
      "hours": 8,
      "priority": "высокий|средний|низкий",
      "role": "backend|frontend|devops|qa|ux|pm",
      "depends_on": []
    }}
  ],
  "critical_paths": []
}}

Требования:
- Верни ТОЛЬКО JSON без JSON внутри ```json``` блока.
- Hours — целое число.
- Поля role/priority — из указанных значений.

Входные данные:
Название проекта: {title}
ТЗ: {spec_text}

Верни только JSON (или JSON в ```json``` блоке).
"""

        messages = [
            {"role": "system", "content": "Ты — проект-аналитик, создающий планы для разработки."},
            {"role": "user", "content": prompt}
        ]

        raw_response = await llm_service.chat(messages, temperature=0.0, max_tokens=2000)

        # Извлекаем JSON
        json_block = _extract_json_block(raw_response)
        if not json_block:
            raise ValueError(f"Не удалось извлечь JSON из ответа модели: {raw_response[:500]}")

        try:
            parsed = json.loads(json_block)
        except json.JSONDecodeError as e:
            # Пробуем убрать комментарии
            cleaned = re.sub(r"//.*?$", "", json_block, flags=re.MULTILINE)
            try:
                parsed = json.loads(cleaned)
            except Exception as e2:
                raise ValueError(f"JSON парсинг не удался: {e}. Очищенный: {e2}")
        
        return parsed

    def estimate_cost(
        self, 
        tasks: List[Dict[str, Any]], 
        rates: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Оценивает стоимость проекта на основе задач.
        """
        if rates is None:
            rates = DEFAULT_RATES_PER_HOUR
        
        breakdown = []
        total = 0.0
        
        for t in tasks:
            hours = int(t.get("hours", 0))
            role = t.get("role", "default")
            rate = rates.get(role, rates["default"])
            cost = hours * rate
            
            breakdown.append({
                "id": t.get("id"),
                "title": t.get("title"),
                "hours": hours,
                "role": role,
                "rate": rate,
                "cost": cost
            })
            total += cost
        
        return {"breakdown": breakdown, "total": total}

    def estimate_timeline(
        self,
        tasks: List[Dict[str, Any]],
        project_start: datetime = None,
        daily_capacity_hours: int = 6
    ) -> Dict[str, Any]:
        """
        Оценивает сроки проекта.
        """
        if project_start is None:
            project_start = datetime.now()

        # Создаём карту задач по id
        id_map = {t["id"]: t for t in tasks}
        
        # Вычисляем зависимости
        deps_map = {tid: set(id_map[tid].get("depends_on", [])) for tid in id_map}
        for k in deps_map:
            deps_map[k] = {d for d in deps_map[k] if d in id_map}

        # Топологическая сортировка
        remaining = set(id_map.keys())
        ordered = []
        
        while remaining:
            ready = [r for r in remaining if not deps_map[r]]
            if not ready:
                ready = list(remaining)
            
            for r in ready:
                ordered.append(id_map[r])
                remaining.remove(r)
                for k in deps_map:
                    deps_map[k].discard(r)

        # Вычисляем расписание
        def hours_to_days(h):
            return max(1, (h + daily_capacity_hours - 1) // daily_capacity_hours)

        dates_for_id = {}
        role_next_free = {}

        for t in ordered:
            role = t.get("role", "default")
            hours = int(t.get("hours", 0))
            duration_days = hours_to_days(hours)
            
            # Вычисляем earliest_start
            deps = t.get("depends_on", []) or []
            deps_end = [
                datetime.strptime(dates_for_id[d]["end_date"], "%d.%m.%Y") 
                for d in deps if d in dates_for_id
            ]
            
            earliest = project_start
            if deps_end:
                latest_dep_end = max(deps_end)
                earliest = max(earliest, latest_dep_end + timedelta(days=1))
            
            role_free = role_next_free.get(role, project_start)
            start = max(earliest, role_free)
            end = start + timedelta(days=duration_days - 1)
            
            # Добавляем буфер 20%
            buffer_days = max(0, int(round(duration_days * 0.2)))
            end_with_buffer = end + timedelta(days=buffer_days)
            
            dates_for_id[t["id"]] = {
                "id": t["id"],
                "title": t.get("title"),
                "role": role,
                "hours": hours,
                "start_date": _format_date(start),
                "end_date": _format_date(end_with_buffer),
                "duration_days": duration_days + buffer_days,
                "depends_on": deps
            }
            
            role_next_free[role] = end_with_buffer + timedelta(days=1)

        # Итоговые даты
        if dates_for_id:
            project_end = max(
                datetime.strptime(v["end_date"], "%d.%m.%Y") 
                for v in dates_for_id.values()
            )
        else:
            project_end = project_start
        
        total_days = (project_end - project_start).days + 1

        # Дни по ролям
        role_days = {}
        for v in dates_for_id.values():
            role_days.setdefault(v["role"], 0)
            role_days[v["role"]] += v["duration_days"]

        return {
            "project_start": _format_date(project_start),
            "project_end": _format_date(project_end),
            "total_work_days": total_days,
            "role_days": role_days,
            "task_schedule": list(dates_for_id.values())
        }

    async def analyze_project(
        self, 
        title: str, 
        spec_text: str
    ) -> Dict[str, Any]:
        """
        Полный анализ проекта: задачи, стоимость, сроки.
        """
        # 1) Генерируем задачи из ТЗ
        parsed = await self.generate_tasks_from_spec(title, spec_text)
        
        tasks = parsed.get("tasks", [])
        
        # 2) Оценка стоимости
        cost = self.estimate_cost(tasks)
        
        # 3) Оценка сроков
        timeline = self.estimate_timeline(tasks, project_start=datetime.now())

        return {
            "project": parsed.get("project", {"title": title, "summary": ""}),
            "tasks": tasks,
            "critical_paths": parsed.get("critical_paths", []),
            "cost_estimate": cost,
            "timeline_estimate": timeline,
            "generated_at": _format_date(datetime.now())
        }


# Синглтон сервиса
analyst_service = AnalystService()

