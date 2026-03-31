"""Structured logging configuration using Loguru.

Supports multiple formats:
- logfmt: key=value pairs (default, machine-readable)
- json: JSON lines for log aggregation
- pretty: Human-readable for development
"""

import logging
import sys
from typing import Any

from loguru import Logger, logger

# Remove default handler
logger.remove()


def format_logfmt(record: dict[str, Any]) -> str:
    """Format log record as logfmt (key=value pairs).

    Example: ts=2024-01-15T10:30:00Z level=INFO msg="User created" user_id=123
    """
    # Base fields
    parts = [
        f"ts={record['time'].isoformat()}",
        f"level={record['level'].name}",
        f"msg={record['message']!r}",
    ]

    # Add extra fields from bind()
    if record.get("extra"):
        for key, value in record["extra"].items():
            if isinstance(value, str):
                # Escape quotes in strings
                value = value.replace('"', '\\"')
                parts.append(f'{key}="{value}"')
            elif isinstance(value, int | float | bool):
                parts.append(f"{key}={value}")
            else:
                parts.append(f'{key}="{value!s}"')

    # Exception info
    if record.get("exception"):
        parts.append(f'exception="{record["exception"]}"')

    return " ".join(parts) + "\n"


def format_json(record: dict[str, Any]) -> str:
    """Format as JSON for structured logging systems."""
    import orjson

    log_data = {
        "ts": record["time"].isoformat(),
        "level": record["level"].name,
        "msg": record["message"],
        **record.get("extra", {}),
    }
    if record.get("exception"):
        log_data["exception"] = str(record["exception"])
    return orjson.dumps(log_data).decode() + "\n"


def format_pretty(record: dict[str, Any]) -> str:
    """Human-readable format for development."""
    extra = " ".join(f"{k}={v}" for k, v in record.get("extra", {}).items())
    extra_str = f" [{extra}]" if extra else ""
    return f"{record['time']:YYYY-MM-DD HH:mm:ss} | " f"{record['level']: <8} | " f"{record['message']}{extra_str}\n"


def configure_logging(level: str = "INFO", format_type: str = "logfmt", sink: str = "stdout") -> None:
    """Configure Loguru with specified format.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Output format (logfmt, json, pretty)
        sink: Output destination (stdout or file path)

    """
    # Select formatter
    formatters = {
        "logfmt": format_logfmt,
        "json": format_json,
        "pretty": format_pretty,
    }
    formatter: str = formatters.get(format_type, format_logfmt)  # type: ignore

    # Configure sink
    if sink == "stdout":
        output = sys.stdout
    else:
        output = sink

    # Add handler with enqueue for async safety
    logger.add(
        output,
        level=level,
        format=formatter,
        enqueue=True,  # Thread-safe for async
        backtrace=True,
        diagnose=level == "DEBUG",
        serialize=False,
    )

    # Intercept standard library logging
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno  # type: ignore

            logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

    # Replace stdlib logging handlers
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Silence noisy libraries
    for lib in ["aiogram", "sqlalchemy", "asyncpg"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    logger.info("Logging configured", format=format_type, level=level)


def get_logger() -> Logger:
    """Get configured logger instance."""
    return logger
