FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей для psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from transformers import AutoImageProcessor, Swinv2ForImageClassification; AutoImageProcessor.from_pretrained('pamixsun/swinv2_tiny_for_glaucoma_classification'); Swinv2ForImageClassification.from_pretrained('pamixsun/swinv2_tiny_for_glaucoma_classification')"

# Копирование кода приложения
COPY . .

# Порт для FastAPI
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
