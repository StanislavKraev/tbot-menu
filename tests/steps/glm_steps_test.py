import asyncio
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from tests.steps.conftest import (
    UserContext,
    create_callback_query,
    create_message,
    process_callback_update,
    process_update,
)

scenarios("features/general_lead_magnit.feature", features_base_dir=str(Path(__file__).parent.parent))


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return loop.run_until_complete(coro)
        return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ========== Given шаги ==========


@given(parsers.parse("пользователь с ID {user_id:d} в личном чате с ботом"), target_fixture="user_context")
def given_user(user_id: int):
    """Создание контекста пользователя - эта фикстура передается в другие шаги"""
    return UserContext(user_id=user_id, chat_id=0)


@when(parsers.parse("пользователь зашел в чат с ботом и вызвал команду /start"))
def when_user_starts_bot(dispatcher, bot, user_context):
    """Отправка команды /start"""

    async def _impl():
        msg = create_message(user_context, text="/start")
        await process_update(dispatcher, bot, msg)

    run_async(_impl())


@given(parsers.parse("база данных содержит чеклисты для симптомов:"), target_fixture="checklist_db")
def given_checklist_database(datatable) -> dict:
    """Инициализация базы данных с чеклистами из таблицы Gherkin"""
    # TODO: save to DB
    checklists = {}
    for symptom, title, path in datatable[1:]:
        checklists[symptom] = {
            "title": title,
            "file_path": f"/app/checklists/{path}",
        }
    return checklists


# ========== When шаги ==========


@when(parsers.parse('пользователь выбирает кнопку "{button_id}"'))
def when_user_selects_button(dispatcher, bot, user_context, button_id: str):
    """Выбор кнопки с определенным ID"""

    async def _impl():
        # Симулируем callback data
        cb = create_callback_query(user_context, data=button_id)
        await process_callback_update(dispatcher, bot, cb)

    run_async(_impl())


@when(parsers.parse('пользователь выбирает проблему "{symptom}"'))
def when_user_selects_symptom(dispatcher, bot, user_context, symptom: str):
    """Выбор симптома (через callback или текст)"""

    async def _impl():
        # Создаём callback с нужными данными
        cb = create_callback_query(user_context, data=f"symptom:{symptom}")
        await process_callback_update(dispatcher, bot, cb)

    run_async(_impl())


# ========== Then шаги ==========


@then(parsers.re(r"бот отображает приветствие с текстом:\s*(?P<welcome_text>.*)"))
def then_bot_shows_welcome(bot, user_context, welcome_text):
    """Проверка приветственного сообщения"""
    welcome_text = welcome_text.strip().strip('"').strip()
    assert len(user_context.messages_sent) > 0, "Нет отправленных сообщений"
    last_msg = user_context.get_last_message()
    assert welcome_text in last_msg["text"], f"Ожидался текст '{welcome_text}', получено: {last_msg['text']}"


@then("бот отображает кнопки:", target_fixture="symptom_buttons")
def then_bot_shows_symptom_buttons(bot, user_context, datatable):
    """Проверка кнопок выбора проблемы с использованием DataTable"""
    last_msg = user_context.get_last_message()
    markup = last_msg.get("reply_markup", {})

    expected_buttons = dict(datatable[1:])
    actual_buttons = {}

    # Извлекаем кнопки из inline keyboard
    if markup.inline_keyboard:
        for row in markup.inline_keyboard:
            for btn in row:
                if btn.callback_data:
                    actual_buttons[btn.callback_data] = btn.text
                elif btn.url:
                    actual_buttons[btn.text] = btn.text

    for btn_id, btn_text in expected_buttons.items():
        assert btn_id in actual_buttons, f"Кнопка {btn_id} не найдена в {actual_buttons}"
        assert btn_text in actual_buttons[btn_id], f"Текст кнопки {btn_id} не совпадает"

    return expected_buttons


@then(parsers.parse('бот предлагает скачать документ "{document_title}"'))
def then_bot_offers_document(bot, user_context, document_title: str):
    """Проверка предложения скачать документ"""
    last_msg = user_context.get_last_message()
    assert document_title in last_msg["text"], f"Заголовок документа '{document_title}' не найден"


@then(parsers.parse('бот отправляет PDF документ "{filename}"'))
def then_bot_sends_pdf(bot, user_context, filename: str):
    """Проверка отправки PDF документа"""
    assert len(user_context.documents_sent) > 0, "Документы не отправлены"
    last_doc = user_context.documents_sent[-1]
    assert filename in last_doc.get("caption", ""), f"Ожидался файл {filename}"


@then(parsers.parse('бот выводит сообщение с предложением перейти на канал: "{expected_message}"'))
def then_bot_shows_channel_offer(bot, user_context, expected_message: str):
    """Проверка многострочного сообщения с предложением подписки"""
    last_msg = user_context.get_last_message()
    actual_text = last_msg["text"].strip()
    assert expected_message in actual_text
