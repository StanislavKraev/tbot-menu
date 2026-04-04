from aiogram.fsm.state import State, StatesGroup


class GeneralLMStates(StatesGroup):
    """Состояния основного лид-магнита."""

    waiting_for_product = State()  # Выбор товара
    waiting_for_quantity = State()  # Ввод количества
    waiting_for_address = State()  # Ввод адреса
    waiting_for_phone = State()  # Ввод телефона
    waiting_for_confirm = State()  # Подтверждение
