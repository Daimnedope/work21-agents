# Agent Estimator Service - Python FastAPI
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Порт
EXPOSE 8080

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
