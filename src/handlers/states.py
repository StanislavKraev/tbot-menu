from aiogram.fsm.state import State, StatesGroup


class GeneralLMStates(StatesGroup):
    """Состояния основного лид-магнита."""

    waiting_for_symptom = State()  # Выбор основной проблемы
    waiting_for_doc_target = State()  # Выбор источника документа

    waiting_for_address = State()  # Ввод адреса
    waiting_for_phone = State()  # Ввод телефона
    waiting_for_confirm = State()  # Подтверждение
