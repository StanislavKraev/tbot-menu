# Dockerfile
# Stage 1: Build dependencies
FROM python:3.12-alpine AS builder

WORKDIR /build
RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev

RUN pip install --no-cache-dir --user poetry

COPY pyproject.toml ./
RUN python -m pip install --user --no-cache-dir -e .

# Stage 2: Production image
FROM python:3.12-alpine AS production

WORKDIR /app

# Установка только runtime зависимостей
RUN apk add --no-cache libpq

# Копируем установленные пакеты из builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Копируем код
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Не-root пользователь для безопасности
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "src.main"]
