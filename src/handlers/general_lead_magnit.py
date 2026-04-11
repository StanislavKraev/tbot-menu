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


# TODO: !!!!
# NOTE: дружелюбный бот. Эмодзи, короткие сообщения. Интерактив! кнопки, вопросы, опросы.
# NOTE: бэкраунд вопросы/приставания только в удообное для пользователя время.
# TODO: 1. параметризовать команду /start, чтобы general lead magnit был дефолтным сценарием для не-подписчиков
# TODO: 2. после окончания GLM сценария переходим к background reminder (BR) сценарию, начиная с шага, на котором
#          остановился пользователь. Только для не-подписчиков.
#          BR сценарий: (в него не перейти пока не окончил GLM сценарий)
#          - После окончания пред. сценария, сразу (одноразово): Спасибо! Давайте познакомимся. Как вас зовут?
#          - Очень приятно!
#          - А какой у вас самый сложный приём пищи в течение дня — завтрак, обед или ужин? ----- это специфично в зависимости от пред. ответов
#            (это поможет мне присылать вам самые полезные советы)
#            Кнопки: Завтрак / Обед / Ужин / Всё сложно
#            Поняла! Запомнила.
# 2-4 часа
#          Отправляем короткий совет, связанный с выбранным сегментом и ответом про приём пищи.
# Не ссылаемся на канал, просто даём пользу здесь и сейчас.
#
# Пример для сегмента «Постоянная усталость» + ответ «Завтрак»:
#
# [Имя], знаете, что большинство мам с усталостью упускают в завтраке? Белок.
# Попробуйте завтра добавить 2 яйца или горсть творога — через 3 дня заметите, что энергия держится дольше.
# У меня в канале как раз недавно разбирала 3 быстрых завтрака с высоким белком. Хотите ссылку?
#           Кнопки: Да, пришли / Пока не надо
#           Если «Да» → отправляем ссылку на конкретный пост в канале.
#           Если «Пока не надо» → бот говорит: «Хорошо, сохраню для вас. Если передумаете — просто напишите "завтраки"».
#
#  Через 1 день — «продолжение истории» (ручная обработка сначала с fallback до дефолта)
# [Имя], сегодня у Жени в канале вышел пост, который вам точно зайдёт: «Как я перестала доедать за детьми и похудела без диет».
# Почитайте, если есть 3 минуты: [ссылка на пост]
# Без кнопок. Просто ссылка.
#
# Через 2–3 дня — мягкое приглашение с акцентом на ценность
# [Имя], вы уже заметили, что я делюсь простыми шагами к здоровью. В моём канале это выходит каждый день: ----- это специфично в зависимости от пред. ответов
# ✅ лайфхаки для мам,
# ✅ разборы анализов,
# ✅ рецепты, которые спасают, когда времени нет.
#
# Подпишитесь, чтобы не пропускать новое:
# [кнопка «Перейти в канал»]
#
#
#
#          При /start для подписчиков ничего не происходит.
# TODO: 3. Сделать для подписчиков background сценарий:
#          - спустя 2 дня после последней коммуникации спросить, любит ли групповой формат общения или больше нравится
#            индивидуальный (расписать, что как детально и спросить)
#              - любит групповые. Сказать, что скоро будет новая группа (дата), посвященная ... Напомнить (да/в другой раз)
#              - индивидуальные. Перекинуть в сценарий "беспокоит ли сейчас что-то" -> выбор услуги / ссылки на статьи
#          - через 2 дня рассказать о доступных скидках (если пользователь хочет)
#          - timeout: интерес есть - 1 день, нет - 1 неделя
#          - А вы знаете, что есть бесплатный разбор анализов? Про второе мнение и т.п. (короче, про врачей и то, как сделать их полезнее)
#            Как это работает: ....
#            Инетерсно - расскажите кратко о своей проблеме и приложите анализы, которые есть на руках.
#            Поделитесь контактом и Женя с вами свяжется в течение пары дней.
#           - Через 2 дня (если не погашен) - спрашиваем, связались ли с вами? нет - сейчас напомню Жене.
#                                                                              да - супер!
#          - супер-секретные методички за подписку. Отправь кому-нибудь, когда он подпишется, будет подарок на выбор!
#            А если подпишутся прям много-много, будет супер-приз!


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
    async def handle_symptom(callback: types.CallbackQuery, state: FSMContext) -> None:
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
        await asyncio.sleep(2.0)  # TODO
        await callback.message.answer(
            f"""✅ Готово! Вы получили {CHECKLIST_TITLE}.
А ещё Женя каждый день делится простыми лайфхаками для здоровья всей семьи в своём канале.
Подписывайтесь, чтобы не пропустить полезное:""",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        await state.clear()

    return general_lm_router
