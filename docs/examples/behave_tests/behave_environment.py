import asyncio


def before_all(context):
    """Запускается один раз перед всеми тестами."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_test_environment(context))


def after_all(context):
    """Запускается один раз после всех тестов."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(stop_test_environment(context))


def before_scenario(context, scenario):
    """Перед каждым сценарием."""
    context.dialog = None  # Сброс контекста диалога


def after_scenario(context, scenario):
    """После каждого сценария — очистка состояний."""
    if hasattr(context, "dialog") and context.dialog:
        # Очистка состояния в БД
        asyncio.get_event_loop().run_until_complete(clear_test_data(context))


async def clear_test_data(context):
    """Удаляет тестовые данные."""
    from sqlalchemy import text

    async with context.db_engine.connect() as conn:
        await conn.execute(
            text("DELETE FROM dialog_states WHERE user_id = :user_id"), {"user_id": context.dialog.user.id}
        )
        await conn.commit()
