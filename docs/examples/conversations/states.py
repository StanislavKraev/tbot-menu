from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Состояния оформления заказа."""

    waiting_for_product = State()  # Выбор товара
    waiting_for_quantity = State()  # Ввод количества
    waiting_for_address = State()  # Ввод адреса
    waiting_for_phone = State()  # Ввод телефона
    waiting_for_confirm = State()  # Подтверждение
