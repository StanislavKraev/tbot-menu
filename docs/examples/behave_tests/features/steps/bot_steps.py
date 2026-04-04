import asyncio

from behave import given, then, when
from behave.api.async_step import async_run_until_complete
from features.steps.context import DialogContext, TestUser

# =============================================================================
# GIVEN - Предусловия
# =============================================================================


@given('новый пользователь с ID "{user_id:d}"')
@async_run_until_complete
async def step_new_user(context, user_id: int):
    """Создает нового тестового пользователя."""
    context.dialog = DialogContext(
        user=TestUser(id=user_id, username=f"user_{user_id}"),
        chat_id=user_id,  # В личном чате chat_id = user_id
    )


@given('пользователь в группе "{chat_id:d}" в топике "{thread_id:d}"')
@async_run_until_complete
async def step_user_in_topic(context, chat_id: int, thread_id: int):
    """Создает пользователя в конкретном топике группы."""
    context.dialog = DialogContext(user=TestUser(id=111111), chat_id=chat_id, thread_id=thread_id)


@given("пользователь уже начал заказ")
@async_run_until_complete
async def step_user_started_order(context):
    """Предустановленное состояние диалога."""
    await context.bot_client.send_message(
        context.dialog.user, "/order", context.dialog.chat_id, context.dialog.thread_id
    )
    context.dialog.add_message("in", "/order", command=True)

    # Проверяем что состояние установлено
    response = await context.bot_client.send_message(
        context.dialog.user,
        "1",  # Выбираем товар
        context.dialog.chat_id,
        context.dialog.thread_id,
    )
    context.dialog.add_message("out", response)


# =============================================================================
# WHEN - Действия
# =============================================================================


@when('пользователь отправляет команду "{command}"')
@async_run_until_complete
async def step_send_command(context, command: str):
    """Отправляет команду боту."""
    response = await context.bot_client.send_message(
        context.dialog.user, f"/{command}", context.dialog.chat_id, context.dialog.thread_id
    )
    context.dialog.add_message("in", f"/{command}", command=True)
    context.dialog.last_response = response

    if response:
        context.dialog.add_message("out", response)


@when('пользователь вводит "{text}"')
@async_run_until_complete
async def step_send_text(context, text: str):
    """Отправляет текстовое сообщение."""
    response = await context.bot_client.send_message(
        context.dialog.user, text, context.dialog.chat_id, context.dialog.thread_id
    )
    context.dialog.add_message("in", text)
    context.dialog.last_response = response

    if response:
        context.dialog.add_message("out", response)


@when('пользователь выбирает товар номер "{product_number:d}"')
@async_run_until_complete
async def step_select_product(context, product_number: int):
    """Выбор товара в диалоге заказа."""
    await step_send_text(context, str(product_number))


@when('проходит "{seconds:d}" секунд')
@async_run_until_complete
async def step_wait(context, seconds: int):
    """Имитация ожидания."""
    await asyncio.sleep(seconds)


# =============================================================================
# THEN - Проверки
# =============================================================================


@then('бот отвечает сообщением содержащим "{expected_text}"')
@async_run_until_complete
async def step_check_response_contains(context, expected_text: str):
    """Проверяет что ответ бота содержит текст."""
    assert context.dialog.last_response, "Нет ответа от бота"
    assert (
        expected_text in context.dialog.last_response
    ), f"Ожидали '{expected_text}' в '{context.dialog.last_response}'"


@then("бот отвечает кнопками")
@async_run_until_complete
async def step_check_buttons(context):
    """Проверяет наличие inline кнопок."""
    # Проверяем через мок или API что ответ содержит reply_markup
    last_msg = get_last_message_with_markup(context.dialog.user.id, context.dialog.chat_id, context.dialog.thread_id)
    assert last_msg.get("reply_markup"), "Нет кнопок в ответе"


@then('в БД сохранено состояние "{state}"')
@async_run_until_complete
async def step_check_db_state(context, state: str):
    """Проверяет FSM состояние в PostgreSQL."""
    from sqlalchemy import text

    async with context.db_engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT state, data
                FROM dialog_states
                WHERE user_id = :user_id
                  AND chat_id = :chat_id
                  AND (thread_id = :thread_id OR (thread_id IS NULL AND :thread_id IS NULL))
            """),
            {
                "user_id": context.dialog.user.id,
                "chat_id": context.dialog.chat_id,
                "thread_id": context.dialog.thread_id,
            },
        )
        row = result.fetchone()

        assert row is not None, "Состояние не найдено в БД"
        assert row.state == state, f"Ожидали состояние '{state}', получили '{row.state}'"

        context.dialog.current_state = row.state


@then('в данных состояния есть поле "{field}" со значением "{value}"')
@async_run_until_complete
async def step_check_state_data(context, field: str, value: str):
    """Проверяет данные в FSM context."""
    import json

    from sqlalchemy import text

    async with context.db_engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT data FROM dialog_states
                WHERE user_id = :user_id AND chat_id = :chat_id
            """),
            {"user_id": context.dialog.user.id, "chat_id": context.dialog.chat_id},
        )
        row = result.fetchone()

        data = json.loads(row.data) if row.data else {}
        assert field in data, f"Поля '{field}' нет в данных"
        assert str(data[field]) == value, f"Ожидали '{field}={value}', получили '{field}={data[field]}'"


@then("состояние очищено")
@async_run_until_complete
async def step_check_state_cleared(context):
    """Проверяет что диалог завершен."""
    from sqlalchemy import text

    async with context.db_engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT COUNT(*) as cnt
                FROM dialog_states
                WHERE user_id = :user_id AND chat_id = :chat_id
            """),
            {"user_id": context.dialog.user.id, "chat_id": context.dialog.chat_id},
        )
        row = result.fetchone()
        assert row.cnt == 0, f"Состояние не очищено, найдено {row.cnt} записей"


@then("история диалога содержит {count:d} сообщений")
def step_check_history_length(context, count: int):
    """Проверяет длину истории."""
    assert (
        len(context.dialog.conversation_history) == count
    ), f"Ожидали {count} сообщений, получили {len(context.dialog.conversation_history)}"


# =============================================================================
# Проверки для USER_IN_TOPIC стратегии
# =============================================================================


@then('в топике {thread_id:d} состояние "{state}"')
@async_run_until_complete
async def step_check_topic_state(context, thread_id: int, state: str):
    """Проверяет изоляцию состояний по топикам."""
    from sqlalchemy import text

    async with context.db_engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT state FROM dialog_states
                WHERE user_id = :user_id
                  AND chat_id = :chat_id
                  AND thread_id = :thread_id
            """),
            {"user_id": context.dialog.user.id, "chat_id": context.dialog.chat_id, "thread_id": thread_id},
        )
        row = result.fetchone()
        assert row and row.state == state, f"В топике {thread_id} ожидали '{state}'"


@given('в топике {thread_id:d} активен заказ на "{product}"')
@async_run_until_complete
async def step_preset_topic_order(context, thread_id: int, product: str):
    """Создает предустановленное состояние в конкретном топике."""
    # Отправляем команду в конкретный топик
    await context.bot_client.send_message(context.dialog.user, "/order", context.dialog.chat_id, thread_id)
    # Выбираем товар
    await context.bot_client.send_message(
        context.dialog.user,
        "1",  # номер товара
        context.dialog.chat_id,
        thread_id,
    )
