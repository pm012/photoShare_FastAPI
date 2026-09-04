FROM python:3.14-alpine

# Встановлюємо системні залежності, необхідні для компіляції psycopg2 та bcrypt
RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev

WORKDIR /app

# Встановлюємо Poetry в систему контейнера
RUN pip install --no-cache-dir poetry

# Вимикаємо створення віртуальних оточень, щоб пакети ставилися прямо в системний Python
RUN poetry config virtualenvs.create false

# Копіюємо конфігурацію залежностей
COPY pyproject.toml poetry.lock* /app/

# Встановлюємо лише основні залежності проєкту (без dev-пакетів для тестів)
RUN poetry install --no-root --only main

# Копіюємо решту коду проєкту
COPY . /app/

# Відкриваємо порт для FastAPI
EXPOSE 8000

# Запуск застосунку
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
