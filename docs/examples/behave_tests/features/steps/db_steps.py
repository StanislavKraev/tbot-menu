from behave import given, then
from behave.api.async_step import async_run_until_complete
from sqlalchemy import text


@given("в БД есть пользователь с заказом")
@async_run_until_complete
async def step_db_has_user_with_order(context):
    """Сид данных для интеграционных тестов."""
    async with context.db_engine.connect() as conn:
        await conn.execute(
            text("""
                INSERT INTO users (telegram_id, username, created_at)
                VALUES (:user_id, :username, NOW())
                ON CONFLICT DO NOTHING
            """),
            {"user_id": context.dialog.user.id, "username": context.dialog.user.username},
        )
        await conn.commit()


@then("в таблице {table_name} {count:d} записей")
@async_run_until_complete
async def step_check_table_count(context, table_name: str, count: int):
    """Проверяет количество записей в таблице."""
    # Валидация имени таблицы для безопасности
    allowed_tables = ["users", "dialog_states", "orders", "pdf_files"]
    assert table_name in allowed_tables, f"Недопустимая таблица: {table_name}"

    async with context.db_engine.connect() as conn:
        result = await conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table_name}"))
        row = result.fetchone()
        assert row.cnt == count, f"В {table_name} ожидали {count} записей, получили {row.cnt}"


@then('заказ пользователя имеет статус "{status}"')
@async_run_until_complete
async def step_check_order_status(context, status: str):
    """Проверяет статус заказа в БД."""
    async with context.db_engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT status FROM orders
                WHERE user_id = :user_id
                ORDER BY created_at DESC LIMIT 1
            """),
            {"user_id": context.dialog.user.id},
        )
        row = result.fetchone()
        assert row and row.status == status, f"Ожидали статус '{status}'"
