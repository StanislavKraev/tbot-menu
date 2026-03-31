import pytest

from src.containers import AppContainer


async def test_user_registration(container: AppContainer) -> None:
    """Тест регистрации пользователя."""
    # Arrange
    telegram_id = 123456789
    username = "testuser"
    utm = "telegram"

    user_service = container.user_service()
    # Act
    user = await user_service.register_user(
        telegram_id=telegram_id,
        username=username,
        first_name="Test",
        last_name="User",
        language_code="ru",
        utm_source=utm,
    )

    # Assert
    assert user["telegram_id"] == telegram_id

    # Проверяем повторную регистрацию (должен вернуть существующего)
    user2 = await user_service.register_user(
        telegram_id=telegram_id,
        username="newname",
        first_name="New",
        last_name="Name",
        language_code="en",
        utm_source="other",
    )
    assert user2["telegram_id"] == telegram_id


@pytest.mark.asyncio
async def test_utm_parsing() -> None:
    """Тест парсинга UTM меток."""
    from src.handlers.start import parse_utm

    assert parse_utm("utm_source=telegram") == "telegram"
    assert parse_utm("telegram") == "telegram"
    assert parse_utm("") is None
