FROM python:3.14-alpine AS builder

RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev
RUN pip install --no-cache-dir poetry==2.4.2

WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

FROM python:3.14-alpine

RUN apk add --no-cache libpq libffi
RUN addgroup -S app && adduser -S -G app app
WORKDIR /app

COPY --from=builder /usr/local /usr/local
COPY --chown=app:app . /app/

USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
