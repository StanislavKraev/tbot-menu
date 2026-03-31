FROM python:3.13-alpine AS builder

WORKDIR /build
RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev

COPY pyproject.toml ./
COPY uv.lock ./

RUN pip install uv \
 && UV_PYTHON=/usr/local/bin/python3.13 \
    uv sync --frozen --no-install-project --no-dev


FROM python:3.13-alpine AS production

WORKDIR /app

# Установка только runtime зависимостей
RUN apk add --no-cache libpq

# Копируем установленные пакеты из builder
COPY --from=builder /build/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH

# Копируем код
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# Не-root пользователь для безопасности
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app  \
 && ln -s /app/.venv/bin/alembic /usr/local/bin/alembic
USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "src.main"]
