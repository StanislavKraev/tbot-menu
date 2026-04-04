def parse_utm(payload: str) -> str | None:
    """Парсинг UTM из payload команды /start."""
    if not payload:
        return None

    # Поддержка форматов: /start utm_source=telegram или /start telegram
    if "=" in payload:
        parts = payload.split("=")
        if len(parts) == 2 and parts[0].strip().lower() in ("utm_source", "source"):
            return parts[1].strip()
    return payload.strip()
