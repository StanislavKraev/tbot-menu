import asyncio
from typing import Any

import aiohttp
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from ..services.user_service import UserService
from .start import parse_utm
from .states import GeneralLMStates

SYMPTOM_TIRED = "tired"
SYMPTOM_WEIGHT = "weight"
SYMPTOM_CJUNK = "cjunk"
SYMPTOM_ANALYSIS = "analysis"

HANDFUL_GUIDE = "Спасибо! У нас как раз есть полезный гайд для вас.\n\nКуда отправить? Выберите удобный вариант:"

BOT_ID = "KraevaNutriciologBot"
CHECKLIST_FILE_ID = "123123123213"
CHECKLIST_TITLE = "Гайд по здоровью"
YANDEX_OAUTH_TOKEN = "todo"  # NoQA  # TODO: get from env


async def get_yandex_direct_link(public_url: str, oauth_token: str) -> Any:
    """Получаем прямую ссылку через API Яндекс.Диска."""
    # Извлекаем ключ из public_url (после /i/)
    file_key = public_url.split("/i/")[-1].split("?")[0]

    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {"public_key": f"https://disk.yandex.ru/i/{file_key}"}

    headers = {"Authorization": f"OAuth {oauth_token}"}  # или без токена для публичных

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params=params, headers=headers) as resp:
            data = await resp.json()
            return data.get("href")  # Прямая ссылка на скачивание


def create_general_lm_router() -> Router:
    general_lm_router = Router()

    def get_symptom_inline_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        # Кнопка со ссылкой
        # builder.row(types.InlineKeyboardButton(
        #     text="Наш сайт", url="https://google.com")
        # )

        symptoms = [
            ("🪫 Постоянная усталость", SYMPTOM_TIRED),
            ("⚖️ Лишний вес не уходит", SYMPTOM_WEIGHT),
            ("🍽️ Дети едят что попало", SYMPTOM_CJUNK),
            ("🔬 Хочу разобраться в анализах", SYMPTOM_ANALYSIS),
        ]
        for title, cb_data in symptoms:
            builder.row(types.InlineKeyboardButton(text=title, callback_data=f"symptom:{cb_data}"))

        return builder.as_markup()

    @general_lm_router.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext, user_service: UserService) -> None:
        message_text: str = message.text or ""
        payload = message_text.split(" ", 1)[1] if " " in message_text else ""
        utm_source = parse_utm(payload)

        from_user = message.from_user
        if not from_user:
            return

        logger.info(f"User {from_user.id} started with UTM: {utm_source}")

        # Сохраняем пользователя
        try:
            await user_service.register_user(
                telegram_id=from_user.id,
                username=from_user.username,
                first_name=from_user.first_name,
                last_name=from_user.last_name,
                language_code=from_user.language_code,
                utm_source=utm_source,
            )
        except Exception:  # NoQA
            logger.exception("Failed to register user")
            return

        await state.set_state(GeneralLMStates.waiting_for_symptom)
        await message.answer(
            "Привет! Я бот Жени, семейного нутрициолога и мамы 4 детей 👩‍👧‍👦👧‍\n\n"
            "Расскажу, как питаться без запретов и находить энергию на всё.\n\n"
            "Чтобы я подобрал для вас подарок, скажите, что сейчас беспокоит больше всего?"
            "",
            reply_markup=get_symptom_inline_keyboard(),
        )

    def get_document_source_keyboard(symptom: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        doc_source = [
            ("📲 Отправить сюда (в Telegram)", f"src:telegram:{symptom}"),
            ("🔗 Открыть в браузере (ссылка)", f"src:url:{symptom}"),
        ]
        for title, cb_data in doc_source:
            builder.row(types.InlineKeyboardButton(text=title, callback_data=cb_data))

        return builder.as_markup()

    @general_lm_router.callback_query(StateFilter(GeneralLMStates.waiting_for_symptom), F.data.startswith("symptom:"))
    async def handle_tired(callback: types.CallbackQuery, state: FSMContext) -> None:
        if not callback.data:
            logger.warning("Invalid callback.data (None)")
            return
        if not callback.message:
            logger.warning("Invalid callback.message (None)")
            return
        symptom = callback.data.split(":")[1]
        await callback.message.answer(HANDFUL_GUIDE, reply_markup=get_document_source_keyboard(symptom))
        await callback.answer()  # Важно закрыть "часики" на кнопке
        await state.set_state(GeneralLMStates.waiting_for_doc_target)

    @general_lm_router.callback_query(StateFilter(GeneralLMStates.waiting_for_doc_target), F.data.startswith("src:"))
    async def handle_src(callback: types.CallbackQuery, state: FSMContext) -> None:
        if not callback.data:
            logger.warning("Invalid callback.data (None)")
            return
        if not callback.message:
            logger.warning("Invalid callback.message (None)")
            return
        src, symptom = callback.data.split(":")[1:]
        await callback.answer()
        if src == "telegram":
            await callback.message.answer_document(
                document=CHECKLIST_FILE_ID,  # TODO: from DB
                caption=f"📄 {CHECKLIST_TITLE}",  # TODO: from DB
                parse_mode="HTML",
            )
        else:
            direct_url = await get_yandex_direct_link(
                "https://disk.yandex.ru/i/AbCdEfGh123", oauth_token=YANDEX_OAUTH_TOKEN
            )

            await callback.message.answer_document(
                document=direct_url,  # Telegram попытается скачать
                caption="📄 {CHECKLIST_TITLE}",
            )

        builder = InlineKeyboardBuilder()
        # Добавляем кнопку-ссылку
        builder.row(
            types.InlineKeyboardButton(
                text="Перейти на канал 📢", url=f"https://t.me/{BOT_ID}"
            )  # Замените на вашу ссылку
        )
        await asyncio.sleep(2.0)
        await callback.message.answer(
            f"""✅ Готово! Вы получили {CHECKLIST_TITLE}.
А ещё Женя каждый день делится простыми лайфхаками для здоровья всей семьи в своём канале.
Подписывайтесь, чтобы не пропустить полезное:""",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        await state.clear()

    return general_lm_router
