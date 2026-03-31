# --- СТАДИЯ 1: Сборка (Builder) ---
FROM python:3.13-alpine AS builder

# Устанавливаем системные зависимости, нужные ТОЛЬКО для сборки (компиляции)
RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev

WORKDIR /app

# Устанавливаем uv максимально эффективно
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv /bin/

# Сначала копируем только файлы зависимостей (для кэширования слоев)
COPY pyproject.toml uv.lock ./

# Синхронизируем зависимости.
# --no-install-project говорит uv не искать сам код приложения на этом этапе
RUN uv sync --frozen --no-dev --no-install-project


# --- СТАДИЯ 2: Финальный образ (Runner) ---
FROM python:3.13-alpine

WORKDIR /app

# Устанавливаем только рантайм-библиотеку для Postgres (она весит копейки)
# Без libpq зависимости вроде psycopg2/asyncpg не заработают
RUN apk add --no-cache libpq

# Создаем пользователя заранее
RUN adduser -D -u 1000 appuser

# Копируем только виртуальное окружение из билдера
# Важно: копируем сразу с правильными правами через --chown
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Копируем код приложения
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --chown=appuser:appuser alembic.ini ./

# Настраиваем окружение
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

USER appuser

# Ссылка на alembic теперь будет работать через PATH
CMD ["python", "-m", "src.main"]
