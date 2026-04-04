import asyncio
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from src.handlers.general_lead_magnit import GeneralLMStates
from tests.steps.conftest import UserContext

scenarios("features/order.feature", features_base_dir=str(Path(__file__).parent.parent))


def run_async(coro):
    """Универсальный запуск корутины из синхронного кода"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return loop.run_until_complete(coro)
        return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ========== Given шаги ==========


@given(parsers.parse("пользователь с ID {user_id:d} в чате {chat_id:d}"), target_fixture="user_context")
def given_user(user_id: int, chat_id: int):
    """Создание контекста пользователя - эта фикстура передается в другие шаги"""
    return UserContext(user_id=user_id, chat_id=chat_id)


@given(parsers.parse('пользователь находится в состоянии выбора количества товара "{product}"'))
def given_user_in_quantity_state(fsm_context, product: str):
    """Установка состояния диалога напрямую в БД"""

    async def _impl() -> None:
        await fsm_context.set_state(GeneralLMStates.waiting_for_quantity)
        await fsm_context.update_data(product=product, price=120000, product_id="1")

    run_async(_impl())


@given(parsers.parse("пользователь в состоянии {state}"))
def given_user_in_state(fsm_context, state: str):
    """Установка произвольного состояния"""

    async def _impl():
        # Маппинг строки на объект State
        state_map = {
            "waiting_for_product": GeneralLMStates.waiting_for_product,
            "waiting_for_quantity": GeneralLMStates.waiting_for_quantity,
            "waiting_for_address": GeneralLMStates.waiting_for_address,
            "waiting_for_phone": GeneralLMStates.waiting_for_phone,
            "waiting_for_confirm": GeneralLMStates.waiting_for_confirm,
        }
        await fsm_context.set_state(state_map.get(state))

    run_async(_impl())


# ========== When шаги ==========


@when(parsers.parse('пользователь отправляет команду "{command}"'))
def when_send_command(dispatcher, bot, user_context, command: str):
    """Отправка команды (/order, /cancel и т.д.)"""

    async def _impl():
        from tests.steps.conftest import create_message, process_update

        msg = create_message(user_context, text=f"/{command}")
        await process_update(dispatcher, bot, msg)

    run_async(_impl())


@when(parsers.parse('пользователь выбирает товар "{product_id}"'))
def when_select_product(dispatcher, bot, user_context, product_id: str):
    """Выбор товара по номеру"""

    async def _impl():
        from tests.steps.conftest import create_message, process_update

        msg = create_message(user_context, text=product_id)
        await process_update(dispatcher, bot, msg)

    run_async(_impl())


@when(parsers.parse('пользователь вводит количество "{quantity:d}"'))
def when_enter_quantity(dispatcher, bot, user_context, quantity: int):
    """Ввод количества"""

    async def _impl():
        from tests.steps.conftest import create_message, process_update

        msg = create_message(user_context, text=str(quantity))
        await process_update(dispatcher, bot, msg)

    run_async(_impl())


@when(parsers.parse('пользователь вводит адрес "{address}"'))
def when_enter_address(dispatcher, bot, user_context, address: str):
    """Ввод адреса"""

    async def _impl():
        from tests.steps.conftest import create_message, process_update

        msg = create_message(user_context, text=address)
        await process_update(dispatcher, bot, msg)

    run_async(_impl())


@when(parsers.parse('пользователь вводит телефон "{phone}"'))
def when_enter_phone(dispatcher, bot, user_context, phone: str):
    """Ввод телефона"""

    async def _impl():
        from tests.steps.conftest import create_message, process_update

        msg = create_message(user_context, text=phone)
        await process_update(dispatcher, bot, msg)

    run_async(_impl())


@when(parsers.parse('пользователь подтверждает заказ "{confirmation}"'))
def when_confirm_order(dispatcher, bot, user_context, confirmation: str):
    """Подтверждение заказа"""

    async def _impl():
        from tests.steps.conftest import create_message, process_update

        msg = create_message(user_context, text=confirmation)
        await process_update(dispatcher, bot, msg)

    run_async(_impl())


# ========== Then шаги ==========


@then("бот запрашивает выбор товара")
def then_asks_for_product(bot, user_context):
    """Проверка запроса товара"""
    assert len(user_context.messages_sent) > 0, "Нет отправленных сообщений"
    last_msg = user_context.get_last_message()
    assert "Выберите товар" in last_msg["text"]
    assert "iPhone 15 Pro" in last_msg["text"]


@then("бот просит ввести количество")
def then_asks_for_quantity(bot, user_context):
    """Проверка запроса количества"""
    last_msg = user_context.get_last_message()
    assert "Введите количество" in last_msg["text"]


@then(parsers.parse('бот показывает итог "{total}" ₽'))
def then_shows_total(bot, user_context, total: str):
    """Проверка отображения итоговой суммы"""
    last_msg = user_context.get_last_message()
    assert f"Итого: <b>{total}" in last_msg["text"] or f"Цена: {total}" in last_msg["text"]


@then("бот просит адрес доставки")
def then_asks_for_address(bot, user_context):
    last_msg = user_context.get_last_message()
    assert "Введите адрес доставки" in last_msg["text"]


@then("бот просит номер телефона")
def then_asks_for_phone(bot, user_context):
    last_msg = user_context.get_last_message()
    assert "номер телефона" in last_msg["text"]


@then("бот показывает сводку заказа")
def then_shows_summary(bot, user_context):
    last_msg = user_context.get_last_message()
    assert "Проверьте заказ" in last_msg["text"]


@then(parsers.parse('в сводке указан товар "{product}"'))
def then_summary_contains_product(bot, user_context, product: str):
    # Ищем в последних сообщениях (сводка может быть не последней из-за кнопок)
    texts = [m["text"] for m in user_context.messages_sent[-3:]]
    assert any(product in t for t in texts), f"Товар {product} не найден в {texts}"


@then(parsers.parse('в сводке указана сумма "{amount}" ₽'))
def then_summary_contains_amount(bot, user_context, amount: str):
    texts = [m["text"] for m in user_context.messages_sent[-3:]]
    assert any(amount in t for t in texts)


@then("бот подтверждает оформление заказа")
def then_confirms_order(bot, user_context):
    last_msg = user_context.get_last_message()
    assert "Заказ оформлен" in last_msg["text"] or "заказ оформлен" in last_msg["text"]


@then("номер заказа отображается в ответе")
def then_shows_order_number(bot, user_context):
    last_msg = user_context.get_last_message()
    assert "#" in last_msg["text"] and any(c.isdigit() for c in last_msg["text"])


@then("бот подтверждает отмену диалога")
def then_confirms_cancel(bot, user_context: UserContext):
    last_msg = user_context.get_last_message()
    assert "отменен" in last_msg["text"].lower()


@then(parsers.parse('состояние диалога "{state}"'))
def then_state_is(fsm_context, state: str):
    """Проверка FSM состояния в БД"""

    async def _impl():
        current = await fsm_context.get_state()
        assert current == state, f"Ожидалось {state}, получено {current}"

    run_async(_impl())


@then("состояние диалога сброшено")
def then_state_cleared(fsm_context):
    """Проверка очистки состояния"""

    async def _impl():
        current = await fsm_context.get_state()
        assert current is None, f"Состояние не сброшено: {current}"

    run_async(_impl())


@then(parsers.parse('состояние диалога остается "{state}"'))
def then_state_remains(fsm_context, state: str):
    """Проверка, что состояние не изменилось"""

    async def _impl():
        current = await fsm_context.get_state()
        assert current == state, f"Ожидалось {state}, получено {current}"

    run_async(_impl())


@then(parsers.parse("бот просит ввести число от 1 до 3"))
def then_asks_for_valid_product(bot, user_context):
    """Проверка валидации ввода"""
    last_msg = user_context.get_last_message()
    assert "Введите число от 1 до 3" in last_msg["text"]
