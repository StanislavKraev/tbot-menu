FROM python:3.13-alpine AS builder

WORKDIR /app
#RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev
RUN apk add --no-cache libffi-dev postgresql-dev libpq

COPY pyproject.toml ./
COPY uv.lock ./
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./

RUN pip install uv \
 && UV_PYTHON=/usr/local/bin/python3.13 \
    uv sync --frozen --no-install-project --no-dev


# Копируем установленные пакеты из builder
ENV PATH=/app/.venv/bin:$PATH

RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app  \
 && ln -s /app/.venv/bin/alembic /usr/local/bin/alembic
USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.main"]
