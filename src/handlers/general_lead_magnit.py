from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from .states import GeneralLMStates

general_lm_router = Router()


@general_lm_router.message(Command("order"))
async def cmd_order(message: types.Message, state: FSMContext) -> None:
    """Начало диалога заказа."""
    await state.set_state(GeneralLMStates.waiting_for_product)
    await message.answer(
        "🛍 <b>Новый заказ</b>\n\n"
        "Выберите товар:\n"
        "1. iPhone 15 Pro - 120000₽\n"
        "2. MacBook Air - 150000₽\n"
        "3. AirPods Pro - 25000₽\n\n"
        "Введите номер товара (1-3):"
    )


@general_lm_router.message(GeneralLMStates.waiting_for_product)
async def process_product(message: types.Message, state: FSMContext) -> None:
    """Обработка выбора товара."""
    if message.text not in ["1", "2", "3"]:
        await message.answer("❌ Введите число от 1 до 3")
        return

    products = {"1": ("iPhone 15 Pro", 120000), "2": ("MacBook Air", 150000), "3": ("AirPods Pro", 25000)}

    product_name, price = products[message.text]

    # Сохраняем в состояние (в БД)
    await state.update_data(product=product_name, price=price, product_id=message.text)

    await state.set_state(GeneralLMStates.waiting_for_quantity)
    await message.answer(f"✅ Выбрано: <b>{product_name}</b>\n" f"💰 Цена: {price}₽\n\n" f"Введите количество:")


@general_lm_router.message(GeneralLMStates.waiting_for_quantity)
async def process_quantity(message: types.Message, state: FSMContext) -> None:
    """Обработка количества."""
    try:
        if not message.text:
            raise ValueError("Must enter count")
        quantity = int(message.text)
        if quantity < 1 or quantity > 10:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число от 1 до 10")
        return

    data = await state.get_data()
    total = data["price"] * quantity

    await state.update_data(quantity=quantity, total=total)
    await state.set_state(GeneralLMStates.waiting_for_address)

    await message.answer(
        f"📦 Количество: <b>{quantity}</b>\n" f"💵 Итого: <b>{total}₽</b>\n\n" f"Введите адрес доставки:"
    )


@general_lm_router.message(GeneralLMStates.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext) -> None:
    """Обработка адреса."""
    await state.update_data(address=message.text)
    await state.set_state(GeneralLMStates.waiting_for_phone)

    await message.answer("📍 Адрес сохранен!\n\n" "Введите номер телефона для связи:")


@general_lm_router.message(GeneralLMStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext) -> None:
    """Обработка телефона и показ сводки."""
    await state.update_data(phone=message.text)
    await state.set_state(GeneralLMStates.waiting_for_confirm)

    data = await state.get_data()

    await message.answer(
        f"📋 <b>Проверьте заказ:</b>\n\n"
        f"🛍 Товар: {data['product']}\n"
        f"📦 Количество: {data['quantity']}\n"
        f"💵 Сумма: {data['total']}₽\n"
        f"📍 Адрес: {data['address']}\n"
        f"📞 Телефон: {data['phone']}\n\n"
        f"Подтвердить заказ? (да/нет)"
    )


@general_lm_router.message(GeneralLMStates.waiting_for_confirm)
async def process_confirm(message: types.Message, state: FSMContext) -> None:
    """Финальное подтверждение."""
    if not message.text or message.text.lower() not in ["да", "yes", "подтвердить"]:
        await state.clear()
        await message.answer("❌ Заказ отменен. Начните заново /order")
        return

    data = await state.get_data()

    # Здесь сохранение заказа в БД
    # save_order_to_db(data)

    await state.clear()
    await message.answer(
        f"✅ <b>Заказ оформлен!</b>\n\n"
        f"Номер заказа: #12345\n"
        f"Сумма: {data['total']}₽\n\n"
        f"Мы свяжемся с вами по телефону {data['phone']}"
    )


@general_lm_router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    """Отмена диалога."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного диалога")
        return

    await state.clear()
    await message.answer("❌ Диалог отменен. Для нового заказа /order")


@general_lm_router.message(Command("status"))
async def cmd_status(message: types.Message, state: FSMContext) -> None:
    """Проверка текущего состояния (для отладки)."""
    current_state = await state.get_state()
    data = await state.get_data()

    if not current_state:
        await message.answer("Нет активного диалога")
        return

    await message.answer(f"Текущее состояние: <code>{current_state}</code>\n" f"Данные: <pre>{data}</pre>")
