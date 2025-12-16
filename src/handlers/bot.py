"""Telegram bot handlers using aiogram."""

from datetime import date, datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    WebAppInfo,
)

from src.config import get_settings
from src.models.user import Language, SubscriptionType, User
from src.services.ai import ai_service
from src.services.database import db
from src.services.numerology import calculate_compatibility, get_full_profile

settings = get_settings()

# Mini App URL
WEBAPP_URL = "https://dreatrio-yaby.github.io/numerolog-ai/"

# Router for handlers
router = Router()


def get_report_view_keyboard(
    report_id: str, lang: str, instance_id: Optional[str] = None
) -> InlineKeyboardMarkup:
    """Create inline keyboard with button to view report in Mini App."""
    btn_text = "✨ Открыть отчёт" if lang == "ru" else "✨ View Report"
    url = f"{WEBAPP_URL}report.html?id={report_id}"
    if instance_id:
        url += f"&instance={instance_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=btn_text,
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )


# FSM States
class OnboardingStates(StatesGroup):
    """States for user onboarding."""

    waiting_for_name = State()
    waiting_for_birthdate = State()


class CompatibilityStates(StatesGroup):
    """States for compatibility check."""

    waiting_for_date = State()


class ReportInputStates(StatesGroup):
    """States for collecting report input data."""

    # Name selection report
    waiting_for_name_purpose = State()  # child/business/self
    waiting_for_child_gender = State()  # male/female

    # Compatibility PRO report
    waiting_for_partner_name = State()
    waiting_for_partner_birthdate = State()

    # Year forecast report
    waiting_for_forecast_year = State()

    # Date calendar report
    waiting_for_calendar_month = State()


# Texts
TEXTS = {
    "ru": {
        "welcome": "✨ Привет! Я AI-нумеролог.\n\nДавай узнаем твои числа? Для начала скажи, как тебя зовут:",
        "welcome_back": """✨ С возвращением, {name}!

💬 Спроси меня о чём угодно:
• «Повезёт ли мне сегодня в любви?»
• «Когда лучше просить повышение?»
• «Как улучшить здоровье по моим числам?»

Или выбери из меню:""",
        "ask_birthdate": "Отлично, {name}! 🎉\n\nТеперь введи свою дату рождения в формате ДД.ММ.ГГГГ\n(например: 15.03.1990)",
        "invalid_date": "🤔 Не могу разобрать дату. Введи в формате ДД.ММ.ГГГГ (например: 15.03.1990)",
        "profile_created": "🔮 Отлично! Твой профиль создан.\n\nСейчас расскажу о твоих числах...",
        "question_limit": "😔 На сегодня бесплатные вопросы закончились.\n\nХочешь продолжить? Выбери тариф:",
        "question_remaining": "💬 Осталось бесплатных вопросов сегодня: {count}",
        "thinking": "🔮 Анализирую...",
        "compatibility_ask": "👫 Введи дату рождения второго человека (ДД.ММ.ГГГГ):",
        "compatibility_limit": "😔 На этой неделе бесплатные проверки совместимости закончились.\n\nОбновится в понедельник или выбери тариф:",
        "buy_success": "🎉 Спасибо за покупку! Твой тариф {plan} активирован на 30 дней.",
        "help": """🔮 *AI Нумеролог* — твой персональный гид в мире чисел

*Команды:*
/profile — твой нумерологический портрет
/today — прогноз на сегодня
/compatibility — проверить совместимость
/buy — тарифы и покупка
/invite — пригласить друга
/settings — настройки
/help — эта справка

*Просто напиши вопрос* — и я отвечу с учётом твоих чисел!""",
        "invite": "👋 Пригласи друга и получи +10 вопросов + 1 премиум отчёт!\n\nТвоя ссылка:\n{link}",
        "settings": "⚙️ *Настройки*\n\nЯзык: {lang}\nУведомления: {notifications}\nВремя уведомлений: {time}",
        "profile_created_hint": """💡 Ты можешь задавать мне любые вопросы!

• «Какая работа мне подходит?»
• «Как наладить отношения?»
• «Что ждёт меня в финансах?»
• «Когда лучше заняться здоровьем?»

Я отвечу с учётом твоих чисел ✨""",
    },
    "en": {
        "welcome": "✨ Hi! I'm an AI Numerologist.\n\nLet's discover your numbers! First, what's your name?",
        "welcome_back": """✨ Welcome back, {name}!

💬 Ask me anything:
• "Will I be lucky in love today?"
• "When should I ask for a raise?"
• "How to improve health based on my numbers?"

Or choose from menu:""",
        "ask_birthdate": "Great, {name}! 🎉\n\nNow enter your birth date in DD.MM.YYYY format\n(e.g., 15.03.1990)",
        "invalid_date": "🤔 Can't parse the date. Use DD.MM.YYYY format (e.g., 15.03.1990)",
        "profile_created": "🔮 Great! Your profile is created.\n\nLet me tell you about your numbers...",
        "question_limit": "😔 Free questions for today are used up.\n\nWant to continue? Choose a plan:",
        "question_remaining": "💬 Free questions remaining today: {count}",
        "thinking": "🔮 Analyzing...",
        "compatibility_ask": "👫 Enter the second person's birth date (DD.MM.YYYY):",
        "compatibility_limit": "😔 Free compatibility checks for this week are used up.\n\nResets on Monday or choose a plan:",
        "buy_success": "🎉 Thank you! Your {plan} plan is activated for 30 days.",
        "help": """🔮 *AI Numerologist* — your personal guide to the world of numbers

*Commands:*
/profile — your numerology portrait
/today — today's forecast
/compatibility — check compatibility
/buy — plans and purchase
/invite — invite a friend
/settings — settings
/help — this help

*Just write a question* — and I'll answer based on your numbers!""",
        "invite": "👋 Invite a friend and get +10 questions + 1 premium report!\n\nYour link:\n{link}",
        "settings": "⚙️ *Settings*\n\nLanguage: {lang}\nNotifications: {notifications}\nNotification time: {time}",
        "profile_created_hint": """💡 You can ask me any questions!

• "What job suits me?"
• "How to improve relationships?"
• "What awaits me in finances?"
• "When to focus on health?"

I'll answer based on your numbers ✨""",
    },
}


def get_text(key: str, lang: str = "ru", **kwargs) -> str:
    """Get localized text."""
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def split_message(text: str, max_length: int = 4000) -> list[str]:
    """Split long message into parts, trying to break at paragraph boundaries."""
    if len(text) <= max_length:
        return [text]

    parts = []
    current_part = ""

    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(current_part) + len(para) + 2 <= max_length:
            current_part += ("\n\n" if current_part else "") + para
        else:
            if current_part:
                parts.append(current_part)
            # If single paragraph is too long, split it by sentences
            if len(para) > max_length:
                while para:
                    parts.append(para[:max_length])
                    para = para[max_length:]
                current_part = ""
            else:
                current_part = para

    if current_part:
        parts.append(current_part)

    return parts


def get_main_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    if lang == "ru":
        buttons = [
            [InlineKeyboardButton(text="🔮 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="📅 Прогноз на сегодня", callback_data="today")],
            [InlineKeyboardButton(text="👫 Совместимость", callback_data="compatibility")],
            [InlineKeyboardButton(text="💎 Тарифы", callback_data="buy")],
            [InlineKeyboardButton(text="⚙️ Настройки", web_app=WebAppInfo(url=WEBAPP_URL))],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🔮 My Profile", callback_data="profile")],
            [InlineKeyboardButton(text="📅 Today's Forecast", callback_data="today")],
            [InlineKeyboardButton(text="👫 Compatibility", callback_data="compatibility")],
            [InlineKeyboardButton(text="💎 Plans", callback_data="buy")],
            [InlineKeyboardButton(text="⚙️ Settings", web_app=WebAppInfo(url=WEBAPP_URL))],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_buy_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Get pricing keyboard."""
    if lang == "ru":
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"⭐ LITE — {settings.price_lite}★",
                    callback_data="buy_lite",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"💎 PRO — {settings.price_pro}★",
                    callback_data="buy_pro",
                )
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu")],
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"⭐ LITE — {settings.price_lite}★ (~$4)",
                    callback_data="buy_lite",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"💎 PRO — {settings.price_pro}★ (~$11)",
                    callback_data="buy_pro",
                )
            ],
            [InlineKeyboardButton(text="◀️ Back", callback_data="menu")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Handlers


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """Handle /start command."""
    telegram_id = message.from_user.id

    # Check for deep link payload
    payload = None
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        payload = message.text.split()[1]

        # Handle report deep link
        if payload.startswith("report_"):
            report_id = payload[7:]  # Remove "report_" prefix
            await handle_report_request(message, state, report_id, bot)
            return

        # Handle referral
        if payload.startswith("ref_") and payload[4:].isdigit():
            referrer_id = int(payload[4:])

    # Check if user exists
    user = await db.get_user(telegram_id)

    if user and user.is_onboarded():
        # Existing user with completed onboarding
        lang = user.language.value
        await message.answer(
            get_text("welcome_back", lang, name=user.name),
            reply_markup=get_main_keyboard(lang),
        )
    else:
        # New user or incomplete onboarding
        if user:
            # Existing user - use their stored language preference
            lang = user.language.value
        else:
            # New user - detect from Telegram and create
            lang = "ru" if message.from_user.language_code in ("ru", "uk", "be") else "en"
            user = await db.create_user(
                telegram_id=telegram_id,
                language=Language(lang),
                referred_by=referrer_id,
            )

        # Start onboarding FSM
        await state.update_data(language=lang)
        await state.set_state(OnboardingStates.waiting_for_name)
        await message.answer(get_text("welcome", lang))


@router.message(OnboardingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Process user's name during onboarding."""
    data = await state.get_data()
    lang = data.get("language", "ru")
    name = message.text.strip()

    await state.update_data(name=name)
    await state.set_state(OnboardingStates.waiting_for_birthdate)
    await message.answer(get_text("ask_birthdate", lang, name=name))


@router.message(OnboardingStates.waiting_for_birthdate)
async def process_birthdate(message: Message, state: FSMContext):
    """Process user's birth date during onboarding."""
    data = await state.get_data()
    lang = data.get("language", "ru")

    # Parse date
    birth_date = parse_date(message.text)
    if not birth_date:
        await message.answer(get_text("invalid_date", lang))
        return

    # Get existing user (created at /start) and update with name and birth_date
    name = data.get("name", "User")
    telegram_id = message.from_user.id

    user = await db.get_user(telegram_id)
    if user:
        # Update existing user with onboarding data
        user.name = name
        user.birth_date = birth_date
        user.language = Language(lang)
        await db.update_user(user)
    else:
        # Fallback: create user if somehow doesn't exist
        user = await db.create_user(
            telegram_id=telegram_id,
            name=name,
            birth_date=birth_date,
            language=Language(lang),
        )

    await state.clear()

    # Generate and send profile
    await message.answer(get_text("profile_created", lang))

    thinking_msg = await message.answer(get_text("thinking", lang))

    profile = get_full_profile(user.name, user.birth_date)
    interpretation = await ai_service.generate_profile_interpretation(user, profile)

    await thinking_msg.delete()
    await message.answer(interpretation, reply_markup=get_main_keyboard(lang))

    # Show hint about free-form questions
    await message.answer(get_text("profile_created_hint", lang))


@router.message(Command("profile"))
@router.callback_query(F.data == "profile")
async def cmd_profile(event: Message | CallbackQuery):
    """Show user's numerology profile."""
    message = event.message if isinstance(event, CallbackQuery) else event
    telegram_id = event.from_user.id

    user = await db.get_user(telegram_id)
    if not user:
        await message.answer("Please start with /start first")
        return

    lang = user.language.value
    thinking_msg = await message.answer(get_text("thinking", lang))

    profile = get_full_profile(user.name, user.birth_date)
    interpretation = await ai_service.generate_profile_interpretation(user, profile)

    await thinking_msg.delete()
    await message.answer(interpretation, reply_markup=get_main_keyboard(lang))

    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("today"))
@router.callback_query(F.data == "today")
async def cmd_today(event: Message | CallbackQuery):
    """Show today's forecast."""
    message = event.message if isinstance(event, CallbackQuery) else event
    telegram_id = event.from_user.id

    user = await db.get_user(telegram_id)
    if not user:
        await message.answer("Please start with /start first")
        return

    lang = user.language.value
    thinking_msg = await message.answer(get_text("thinking", lang))

    profile = get_full_profile(user.name, user.birth_date)
    forecast = await ai_service.generate_daily_forecast(user, profile)

    await thinking_msg.delete()
    await message.answer(f"📅 *Прогноз на сегодня*\n\n{forecast}", parse_mode="Markdown")

    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("compatibility"))
@router.callback_query(F.data == "compatibility")
async def cmd_compatibility(event: Message | CallbackQuery, state: FSMContext):
    """Start compatibility check."""
    message = event.message if isinstance(event, CallbackQuery) else event
    telegram_id = event.from_user.id

    user = await db.get_user(telegram_id)
    if not user:
        await message.answer("Please start with /start first")
        return

    lang = user.language.value

    # Check limit for free users
    if not user.is_premium() and not user.can_check_compatibility():
        await message.answer(
            get_text("compatibility_limit", lang),
            reply_markup=get_buy_keyboard(lang),
        )
        if isinstance(event, CallbackQuery):
            await event.answer()
        return

    await state.set_state(CompatibilityStates.waiting_for_date)
    await message.answer(get_text("compatibility_ask", lang))

    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(CompatibilityStates.waiting_for_date)
async def process_compatibility_date(message: Message, state: FSMContext):
    """Process compatibility partner's date."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await state.clear()
        return

    lang = user.language.value

    # Parse date
    partner_date = parse_date(message.text)
    if not partner_date:
        await message.answer(get_text("invalid_date", lang))
        return

    await state.clear()

    # Increment counter for free users
    if not user.is_premium():
        await db.increment_compatibility_this_week(user)

    thinking_msg = await message.answer(get_text("thinking", lang))

    # Calculate compatibility
    compatibility = calculate_compatibility(user.birth_date, partner_date)
    analysis = await ai_service.generate_compatibility_analysis(compatibility, lang)

    await thinking_msg.delete()

    result = f"👫 *Совместимость: {compatibility['overall_score']}%*\n\n{analysis}"
    await message.answer(result, parse_mode="Markdown", reply_markup=get_main_keyboard(lang))


@router.message(Command("buy"))
@router.callback_query(F.data == "buy")
async def cmd_buy(event: Message | CallbackQuery):
    """Show pricing options."""
    message = event.message if isinstance(event, CallbackQuery) else event
    telegram_id = event.from_user.id

    user = await db.get_user(telegram_id)
    lang = user.language.value if user else "ru"

    if lang == "ru":
        text = """💎 *Тарифы*

*FREE* — бесплатно
• 3 вопроса в день
• 2 проверки совместимости в неделю
• Базовый портрет

*LITE* — 175★ на 30 дней
• Безлимит вопросов
• Безлимит совместимости

*PRO* — 500★ на 30 дней
• Всё из LITE
• Все премиум отчёты включены:
  - Полный портрет (120★)
  - Финансовый код (150★)
  - Календарь дат (130★)
  - Прогноз на год (150★)
  - Подбор имени (140★)
  - Совместимость PRO (150★)

💰 Экономия: 840★ → 500★!"""
    else:
        text = """💎 *Plans*

*FREE* — free
• 3 questions per day
• 2 compatibility checks per week
• Basic profile

*LITE* — 175★ (~$4) for 30 days
• Unlimited questions
• Unlimited compatibility

*PRO* — 500★ (~$11) for 30 days
• Everything in LITE
• All premium reports included:
  - Full Portrait (120★)
  - Financial Code (150★)
  - Date Calendar (130★)
  - Year Forecast (150★)
  - Name Selection (140★)
  - Compatibility PRO (150★)

💰 Save: 840★ → 500★!"""

    await message.answer(text, parse_mode="Markdown", reply_markup=get_buy_keyboard(lang))

    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery, bot: Bot):
    """Process purchase request."""
    telegram_id = callback.from_user.id
    plan = callback.data.split("_")[1]  # lite or pro

    user = await db.get_user(telegram_id)
    lang = user.language.value if user else "ru"

    if plan == "lite":
        amount = settings.price_lite
        title = "LITE — 30 дней" if lang == "ru" else "LITE — 30 days"
        description = (
            "Безлимит вопросов и совместимости"
            if lang == "ru"
            else "Unlimited questions and compatibility"
        )
    else:
        amount = settings.price_pro
        title = "PRO — 30 дней" if lang == "ru" else "PRO — 30 days"
        description = (
            "Безлимит + все премиум отчёты" if lang == "ru" else "Unlimited + all premium reports"
        )

    # Send invoice with Telegram Stars
    await bot.send_invoice(
        chat_id=telegram_id,
        title=title,
        description=description,
        payload=f"subscription_{plan}",
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=title, amount=amount)],
    )

    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery, bot: Bot):
    """Handle pre-checkout query."""
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Handle successful payment."""
    telegram_id = message.from_user.id
    payment = message.successful_payment
    payload = payment.invoice_payload

    user = await db.get_user(telegram_id)
    if not user:
        return

    lang = user.language.value

    # Save payment to history
    await db.add_payment(user, payload, payment.total_amount)

    # Activate subscription
    if payload == "subscription_lite":
        user = await db.activate_subscription(user, SubscriptionType.LITE)
        plan_name = "LITE"
    elif payload == "subscription_pro":
        user = await db.activate_subscription(user, SubscriptionType.PRO)
        plan_name = "PRO"
    elif payload.startswith("report_"):
        report_id = payload[7:]
        info = REPORT_INFO.get(report_id, {})
        is_multi = info.get("multi_instance", False)

        # Check if already generating (prevent duplicates from webhook retries)
        if await db.is_report_generating(telegram_id, report_id):
            return
        await db.set_report_generating(telegram_id, report_id)

        await db.add_purchased_report(user, report_id)

        # Send "generating" message
        thinking_text = (
            "🔮 Генерирую твой отчёт..." if lang == "ru" else "🔮 Generating your report..."
        )
        thinking_msg = await message.answer(thinking_text)

        # Get user profile
        profile = get_full_profile(user.name, user.birth_date)

        # Get pending data if needed (for reports with context)
        pending_data = await db.get_pending_report_data(telegram_id, report_id)
        instance_id = None
        context = pending_data or {}

        # Generate report based on type
        if report_id == "full_portrait":
            content = await ai_service.generate_full_portrait_report(user, profile)
        elif report_id == "financial_code":
            content = await ai_service.generate_financial_code_report(user, profile)
        elif report_id == "date_calendar" and pending_data:
            month = pending_data.get("month")
            year = pending_data.get("year")
            content = await ai_service.generate_date_calendar_report(user, profile, month, year)
            await db.delete_pending_report_data(telegram_id, report_id)
        elif report_id == "year_forecast" and pending_data:
            year = pending_data.get("year")
            content = await ai_service.generate_year_forecast_report(user, profile, year)
            await db.delete_pending_report_data(telegram_id, report_id)
        elif report_id == "name_selection" and pending_data:
            content = await ai_service.generate_name_selection_report(user, profile, pending_data)
            await db.delete_pending_report_data(telegram_id, report_id)
        elif report_id == "compatibility_pro" and pending_data:
            # AI service expects 'name' and 'birth_date' keys
            ai_data = {
                "name": pending_data.get("partner_name"),
                "birth_date": pending_data.get("partner_birth_date"),
            }
            content = await ai_service.generate_compatibility_pro_report(user, profile, ai_data)
            await db.delete_pending_report_data(telegram_id, report_id)
        else:
            await thinking_msg.delete()
            await db.clear_report_generating(telegram_id, report_id)
            error_text = (
                "❌ Ошибка генерации отчёта" if lang == "ru" else "❌ Report generation error"
            )
            await message.answer(error_text)
            return

        # Save report to database
        if is_multi:
            instance_id = await db.save_report_instance(telegram_id, report_id, content, context)
        else:
            await db.save_report(telegram_id, report_id, content)
        await db.clear_report_generating(telegram_id, report_id)

        # Delete thinking message
        await thinking_msg.delete()

        # Send button to view report in Mini App
        report_info = REPORT_INFO.get(report_id, {})
        title = report_info.get("name_ru" if lang == "ru" else "name_en", "Отчёт")
        done_text = (
            f"✨ *{title}* готов!\n\nНажми кнопку ниже, чтобы открыть отчёт."
            if lang == "ru"
            else f"✨ *{title}* is ready!\n\nTap the button below to view your report."
        )
        await message.answer(
            done_text,
            parse_mode="Markdown",
            reply_markup=get_report_view_keyboard(report_id, lang, instance_id),
        )
        return
    else:
        return

    await message.answer(
        get_text("buy_success", lang, plan=plan_name),
        reply_markup=get_main_keyboard(lang),
    )


@router.message(Command("invite"))
async def cmd_invite(message: Message):
    """Show invite link."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await message.answer("Please start with /start first")
        return

    lang = user.language.value
    bot_username = (await message.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{telegram_id}"

    await message.answer(get_text("invite", lang, link=invite_link))


# ===== REPORT PURCHASE FLOW =====

REPORT_INFO = {
    "full_portrait": {"price": 120, "name_ru": "Полный портрет", "name_en": "Full Portrait"},
    "financial_code": {"price": 150, "name_ru": "Финансовый код", "name_en": "Financial Code"},
    "date_calendar": {
        "price": 130,
        "name_ru": "Календарь дат",
        "name_en": "Date Calendar",
        "requires_input": True,
        "multi_instance": True,
    },
    "year_forecast": {
        "price": 150,
        "name_ru": "Прогноз на год",
        "name_en": "Year Forecast",
        "requires_input": True,
        "multi_instance": True,
    },
    "name_selection": {
        "price": 140,
        "name_ru": "Подбор имени",
        "name_en": "Name Selection",
        "requires_input": True,
        "multi_instance": True,
    },
    "compatibility_pro": {
        "price": 150,
        "name_ru": "Совместимость PRO",
        "name_en": "Compatibility PRO",
        "requires_input": True,
        "multi_instance": True,
    },
}


async def handle_report_request(message: Message, state: FSMContext, report_id: str, bot: Bot):
    """Handle report request from deep link or callback."""
    telegram_id = message.chat.id
    user = await db.get_user(telegram_id)

    if not user or not user.is_onboarded():
        lang = user.language.value if user else "ru"
        text = (
            "Сначала пройди онбординг командой /start"
            if lang == "ru"
            else "Please complete onboarding with /start first"
        )
        await message.answer(text)
        return

    lang = user.language.value
    is_pro = user.subscription_type.value == "pro" and user.is_premium()
    has_report = report_id in user.purchased_reports
    info = REPORT_INFO.get(report_id)
    is_multi = info.get("multi_instance", False)

    if not info:
        await message.answer("Unknown report")
        return

    # 1. For single-instance reports: already purchased - show button to view
    if has_report and not is_multi:
        existing = await db.get_report(telegram_id, report_id)
        if existing:
            title = info["name_ru"] if lang == "ru" else info["name_en"]
            text = (
                f"📜 *{title}*\n\nТвой отчёт готов к просмотру."
                if lang == "ru"
                else f"📜 *{title}*\n\nYour report is ready to view."
            )
            await message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=get_report_view_keyboard(report_id, lang),
            )
            return

    # 2. PRO + no input needed - generate directly (only for single-instance)
    if is_pro and not info.get("requires_input") and not is_multi:
        # Check if already generating (prevent duplicates from webhook retries)
        if await db.is_report_generating(telegram_id, report_id):
            return
        await db.set_report_generating(telegram_id, report_id)

        thinking_text = "🔮 Генерирую отчёт..." if lang == "ru" else "🔮 Generating report..."
        thinking_msg = await message.answer(thinking_text)

        profile = get_full_profile(user.name, user.birth_date)

        if report_id == "full_portrait":
            content = await ai_service.generate_full_portrait_report(user, profile)
        elif report_id == "financial_code":
            content = await ai_service.generate_financial_code_report(user, profile)
        else:
            await thinking_msg.delete()
            await db.clear_report_generating(telegram_id, report_id)
            return

        await db.save_report(telegram_id, report_id, content)
        await db.add_purchased_report(user, report_id)
        await db.clear_report_generating(telegram_id, report_id)
        await thinking_msg.delete()

        # Send button to view report in Mini App
        title = info["name_ru"] if lang == "ru" else info["name_en"]
        done_text = (
            f"✨ *{title}* готов!\n\nНажми кнопку ниже, чтобы открыть отчёт."
            if lang == "ru"
            else f"✨ *{title}* is ready!\n\nTap the button below to view your report."
        )
        await message.answer(
            done_text,
            parse_mode="Markdown",
            reply_markup=get_report_view_keyboard(report_id, lang),
        )
        return

    # 3. Reports requiring input - start FSM
    if info.get("requires_input"):
        if report_id == "name_selection":
            await state.set_state(ReportInputStates.waiting_for_name_purpose)
            await state.update_data(report_id=report_id, is_pro=is_pro)

            text = (
                "📝 *Подбор имени*\n\nДля кого подбираем имя?"
                if lang == "ru"
                else "📝 *Name Selection*\n\nWho is the name for?"
            )

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👶 Для ребёнка" if lang == "ru" else "👶 For a child",
                            callback_data="name_purpose_child",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="💼 Для бизнеса" if lang == "ru" else "💼 For business",
                            callback_data="name_purpose_business",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=(
                                "✏️ Для себя (ник)" if lang == "ru" else "✏️ For myself (nickname)"
                            ),
                            callback_data="name_purpose_self",
                        )
                    ],
                ]
            )
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
            return

        elif report_id == "compatibility_pro":
            await state.set_state(ReportInputStates.waiting_for_partner_name)
            await state.update_data(report_id=report_id, is_pro=is_pro)

            text = (
                "💑 *Совместимость PRO*\n\nВведи имя партнёра:"
                if lang == "ru"
                else "💑 *Compatibility PRO*\n\nEnter partner's name:"
            )

            await message.answer(text, parse_mode="Markdown")
            return

        elif report_id == "year_forecast":
            await state.set_state(ReportInputStates.waiting_for_forecast_year)
            await state.update_data(report_id=report_id, is_pro=is_pro)

            current_year = datetime.now().year
            text = (
                "📅 *Прогноз на год*\n\nВыбери год для прогноза:"
                if lang == "ru"
                else "📅 *Year Forecast*\n\nSelect year for forecast:"
            )

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=str(current_year),
                            callback_data=f"forecast_year_{current_year}",
                        ),
                        InlineKeyboardButton(
                            text=str(current_year + 1),
                            callback_data=f"forecast_year_{current_year + 1}",
                        ),
                    ],
                ]
            )
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
            return

        elif report_id == "date_calendar":
            await state.set_state(ReportInputStates.waiting_for_calendar_month)
            await state.update_data(report_id=report_id, is_pro=is_pro)

            now = datetime.now()
            current_month = now.month
            current_year = now.year

            # Next month
            if current_month == 12:
                next_month = 1
                next_year = current_year + 1
            else:
                next_month = current_month + 1
                next_year = current_year

            month_names_ru = [
                "",
                "Январь",
                "Февраль",
                "Март",
                "Апрель",
                "Май",
                "Июнь",
                "Июль",
                "Август",
                "Сентябрь",
                "Октябрь",
                "Ноябрь",
                "Декабрь",
            ]
            month_names_en = [
                "",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]

            text = (
                "📆 *Календарь дат*\n\nВыбери месяц:"
                if lang == "ru"
                else "📆 *Date Calendar*\n\nSelect month:"
            )

            if lang == "ru":
                cur_label = f"{month_names_ru[current_month]} {current_year}"
                next_label = f"{month_names_ru[next_month]} {next_year}"
            else:
                cur_label = f"{month_names_en[current_month]} {current_year}"
                next_label = f"{month_names_en[next_month]} {next_year}"

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=cur_label,
                            callback_data=f"calendar_month_{current_month}_{current_year}",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text=next_label,
                            callback_data=f"calendar_month_{next_month}_{next_year}",
                        ),
                    ],
                ]
            )
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
            return

    # 4. Not PRO, not purchased - send invoice
    name = info["name_ru"] if lang == "ru" else info["name_en"]
    desc = f"Премиум отчёт: {name}" if lang == "ru" else f"Premium report: {name}"

    await bot.send_invoice(
        chat_id=telegram_id,
        title=name,
        description=desc,
        payload=f"report_{report_id}",
        currency="XTR",
        prices=[LabeledPrice(label=name, amount=info["price"])],
    )


@router.message(Command("report"))
async def cmd_report(message: Message):
    """Show available reports for purchase."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await message.answer("Please start with /start first")
        return

    lang = user.language.value
    is_pro = user.subscription_type.value == "pro" and user.is_premium()

    if lang == "ru":
        text = "📜 *Премиум отчёты*\n\n"
        if is_pro:
            text += "У тебя PRO — все отчёты доступны бесплатно!\n\n"
    else:
        text = "📜 *Premium Reports*\n\n"
        if is_pro:
            text += "You have PRO — all reports are free!\n\n"

    buttons = []
    for report_id, info in REPORT_INFO.items():
        name = info["name_ru"] if lang == "ru" else info["name_en"]
        has_report = report_id in user.purchased_reports

        if has_report:
            status = " ✅"
        elif is_pro:
            status = " 🆓"
        else:
            status = f" ({info['price']}★)"

        buttons.append(
            [InlineKeyboardButton(text=f"{name}{status}", callback_data=f"report_{report_id}")]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data.startswith("report_"))
async def callback_report(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle report selection from inline keyboard."""
    report_id = callback.data[7:]  # Remove "report_" prefix
    await callback.answer()
    await handle_report_request(callback.message, state, report_id, bot)


# Name selection FSM handlers
@router.callback_query(
    F.data.startswith("name_purpose_"), ReportInputStates.waiting_for_name_purpose
)
async def process_name_purpose(callback: CallbackQuery, state: FSMContext):
    """Handle name purpose selection."""
    purpose = callback.data.replace("name_purpose_", "")

    user = await db.get_user(callback.from_user.id)
    lang = user.language.value if user else "ru"

    await state.update_data(purpose=purpose)

    if purpose == "child":
        await state.set_state(ReportInputStates.waiting_for_child_gender)

        if lang == "ru":
            text = "👶 Выбери пол ребёнка:"
        else:
            text = "👶 Select child's gender:"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👦 Мальчик" if lang == "ru" else "👦 Boy",
                        callback_data="child_gender_male",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👧 Девочка" if lang == "ru" else "👧 Girl",
                        callback_data="child_gender_female",
                    )
                ],
            ]
        )
        await callback.message.answer(text, reply_markup=keyboard)
    else:
        # Business or self - proceed to payment/generation
        await finalize_name_selection(callback, state, user, purpose, None)

    await callback.answer()


@router.callback_query(
    F.data.startswith("child_gender_"), ReportInputStates.waiting_for_child_gender
)
async def process_child_gender(callback: CallbackQuery, state: FSMContext):
    """Handle child gender selection."""
    gender = callback.data.replace("child_gender_", "")
    data = await state.get_data()
    purpose = data.get("purpose", "child")

    user = await db.get_user(callback.from_user.id)
    await finalize_name_selection(callback, state, user, purpose, gender)
    await callback.answer()


async def finalize_name_selection(
    callback: CallbackQuery, state: FSMContext, user: User, purpose: str, gender: Optional[str]
):
    """Finalize name selection - save data and proceed to payment or generate."""
    telegram_id = callback.from_user.id
    lang = user.language.value
    data = await state.get_data()
    is_pro = data.get("is_pro", False)

    # Context for multi-instance report
    context = {"purpose": purpose}
    if gender:
        context["gender"] = gender

    await db.save_pending_report_data(telegram_id, "name_selection", context)
    await state.clear()

    if is_pro:
        # Check if already generating (prevent duplicates from webhook retries)
        if await db.is_report_generating(telegram_id, "name_selection"):
            return
        await db.set_report_generating(telegram_id, "name_selection")

        # Generate directly for PRO users
        thinking_text = "🔮 Генерирую отчёт..." if lang == "ru" else "🔮 Generating report..."
        thinking_msg = await callback.message.answer(thinking_text)

        profile = get_full_profile(user.name, user.birth_date)
        content = await ai_service.generate_name_selection_report(user, profile, context)

        # Save as multi-instance report
        instance_id = await db.save_report_instance(telegram_id, "name_selection", content, context)
        await db.add_purchased_report(user, "name_selection")
        await db.delete_pending_report_data(telegram_id, "name_selection")
        await db.clear_report_generating(telegram_id, "name_selection")
        await thinking_msg.delete()

        # Send button to view report in Mini App
        title = "Подбор имени" if lang == "ru" else "Name Selection"
        done_text = (
            f"✨ *{title}* готов!\n\nНажми кнопку ниже, чтобы открыть отчёт."
            if lang == "ru"
            else f"✨ *{title}* is ready!\n\nTap the button below to view your report."
        )
        await callback.message.answer(
            done_text,
            parse_mode="Markdown",
            reply_markup=get_report_view_keyboard("name_selection", lang, instance_id),
        )
    else:
        # Send invoice
        info = REPORT_INFO["name_selection"]
        name = info["name_ru"] if lang == "ru" else info["name_en"]
        desc = f"Премиум отчёт: {name}" if lang == "ru" else f"Premium report: {name}"

        await callback.message.bot.send_invoice(
            chat_id=telegram_id,
            title=name,
            description=desc,
            payload="report_name_selection",
            currency="XTR",
            prices=[LabeledPrice(label=name, amount=info["price"])],
        )


# Compatibility PRO FSM handlers
@router.message(ReportInputStates.waiting_for_partner_name)
async def process_partner_name(message: Message, state: FSMContext):
    """Handle partner name input."""
    partner_name = message.text.strip()

    user = await db.get_user(message.from_user.id)
    lang = user.language.value if user else "ru"

    await state.update_data(partner_name=partner_name)
    await state.set_state(ReportInputStates.waiting_for_partner_birthdate)

    if lang == "ru":
        text = f"💑 Отлично! Теперь введи дату рождения {partner_name} (ДД.ММ.ГГГГ):"
    else:
        text = f"💑 Great! Now enter {partner_name}'s birth date (DD.MM.YYYY):"

    await message.answer(text)


@router.message(ReportInputStates.waiting_for_partner_birthdate)
async def process_partner_birthdate(message: Message, state: FSMContext, bot: Bot):
    """Handle partner birthdate input."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)
    lang = user.language.value if user else "ru"

    # Parse date
    date_text = message.text.strip()
    partner_birth_date = None

    for fmt in ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"]:
        try:
            partner_birth_date = datetime.strptime(date_text, fmt).date()
            break
        except ValueError:
            continue

    if not partner_birth_date:
        error_text = (
            "🤔 Не могу разобрать дату. Введи в формате ДД.ММ.ГГГГ"
            if lang == "ru"
            else "🤔 Can't parse date. Enter in DD.MM.YYYY format"
        )
        await message.answer(error_text)
        return

    data = await state.get_data()
    partner_name = data.get("partner_name", "Partner")
    is_pro = data.get("is_pro", False)

    # Context for multi-instance report
    context = {"partner_name": partner_name, "partner_birth_date": partner_birth_date.isoformat()}

    await db.save_pending_report_data(telegram_id, "compatibility_pro", context)
    await state.clear()

    if is_pro:
        # Check if already generating (prevent duplicates from webhook retries)
        if await db.is_report_generating(telegram_id, "compatibility_pro"):
            return
        await db.set_report_generating(telegram_id, "compatibility_pro")

        # Generate directly for PRO users
        thinking_text = "🔮 Генерирую отчёт..." if lang == "ru" else "🔮 Generating report..."
        thinking_msg = await message.answer(thinking_text)

        profile = get_full_profile(user.name, user.birth_date)
        # Use 'name' and 'birth_date' keys for AI service compatibility
        pending_data = {"name": partner_name, "birth_date": partner_birth_date.isoformat()}
        content = await ai_service.generate_compatibility_pro_report(user, profile, pending_data)

        # Save as multi-instance report
        instance_id = await db.save_report_instance(
            telegram_id, "compatibility_pro", content, context
        )
        await db.add_purchased_report(user, "compatibility_pro")
        await db.delete_pending_report_data(telegram_id, "compatibility_pro")
        await db.clear_report_generating(telegram_id, "compatibility_pro")
        await thinking_msg.delete()

        # Send button to view report in Mini App
        title = "Совместимость PRO" if lang == "ru" else "Compatibility PRO"
        done_text = (
            f"✨ *{title}* готов!\n\nНажми кнопку ниже, чтобы открыть отчёт."
            if lang == "ru"
            else f"✨ *{title}* is ready!\n\nTap the button below to view your report."
        )
        await message.answer(
            done_text,
            parse_mode="Markdown",
            reply_markup=get_report_view_keyboard("compatibility_pro", lang, instance_id),
        )
    else:
        # Send invoice
        info = REPORT_INFO["compatibility_pro"]
        name = info["name_ru"] if lang == "ru" else info["name_en"]
        desc = f"Премиум отчёт: {name}" if lang == "ru" else f"Premium report: {name}"

        await bot.send_invoice(
            chat_id=telegram_id,
            title=name,
            description=desc,
            payload="report_compatibility_pro",
            currency="XTR",
            prices=[LabeledPrice(label=name, amount=info["price"])],
        )


# Year Forecast FSM handlers
@router.callback_query(
    F.data.startswith("forecast_year_"), ReportInputStates.waiting_for_forecast_year
)
async def process_forecast_year(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle year selection for forecast."""
    year = int(callback.data.replace("forecast_year_", ""))

    user = await db.get_user(callback.from_user.id)
    lang = user.language.value if user else "ru"
    telegram_id = callback.from_user.id

    data = await state.get_data()
    is_pro = data.get("is_pro", False)

    # Context for multi-instance report
    context = {"year": year}

    await db.save_pending_report_data(telegram_id, "year_forecast", context)
    await state.clear()

    if is_pro:
        # Check if already generating
        if await db.is_report_generating(telegram_id, "year_forecast"):
            await callback.answer()
            return
        await db.set_report_generating(telegram_id, "year_forecast")

        thinking_text = "🔮 Генерирую отчёт..." if lang == "ru" else "🔮 Generating report..."
        thinking_msg = await callback.message.answer(thinking_text)

        profile = get_full_profile(user.name, user.birth_date)
        content = await ai_service.generate_year_forecast_report(user, profile, year)

        instance_id = await db.save_report_instance(
            telegram_id, "year_forecast", content, context
        )
        await db.add_purchased_report(user, "year_forecast")
        await db.delete_pending_report_data(telegram_id, "year_forecast")
        await db.clear_report_generating(telegram_id, "year_forecast")
        await thinking_msg.delete()

        title = f"Прогноз на {year}" if lang == "ru" else f"Forecast for {year}"
        done_text = (
            f"✨ *{title}* готов!\n\nНажми кнопку ниже, чтобы открыть отчёт."
            if lang == "ru"
            else f"✨ *{title}* is ready!\n\nTap the button below to view your report."
        )
        await callback.message.answer(
            done_text,
            parse_mode="Markdown",
            reply_markup=get_report_view_keyboard("year_forecast", lang, instance_id),
        )
    else:
        info = REPORT_INFO["year_forecast"]
        name = info["name_ru"] if lang == "ru" else info["name_en"]
        desc = f"Премиум отчёт: {name}" if lang == "ru" else f"Premium report: {name}"

        await bot.send_invoice(
            chat_id=telegram_id,
            title=name,
            description=desc,
            payload="report_year_forecast",
            currency="XTR",
            prices=[LabeledPrice(label=name, amount=info["price"])],
        )

    await callback.answer()


# Date Calendar FSM handlers
@router.callback_query(
    F.data.startswith("calendar_month_"), ReportInputStates.waiting_for_calendar_month
)
async def process_calendar_month(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle month selection for calendar."""
    parts = callback.data.replace("calendar_month_", "").split("_")
    month = int(parts[0])
    year = int(parts[1])

    user = await db.get_user(callback.from_user.id)
    lang = user.language.value if user else "ru"
    telegram_id = callback.from_user.id

    data = await state.get_data()
    is_pro = data.get("is_pro", False)

    # Context for multi-instance report
    context = {"month": month, "year": year}

    await db.save_pending_report_data(telegram_id, "date_calendar", context)
    await state.clear()

    if is_pro:
        # Check if already generating
        if await db.is_report_generating(telegram_id, "date_calendar"):
            await callback.answer()
            return
        await db.set_report_generating(telegram_id, "date_calendar")

        thinking_text = "🔮 Генерирую отчёт..." if lang == "ru" else "🔮 Generating report..."
        thinking_msg = await callback.message.answer(thinking_text)

        profile = get_full_profile(user.name, user.birth_date)
        content = await ai_service.generate_date_calendar_report(user, profile, month, year)

        instance_id = await db.save_report_instance(
            telegram_id, "date_calendar", content, context
        )
        await db.add_purchased_report(user, "date_calendar")
        await db.delete_pending_report_data(telegram_id, "date_calendar")
        await db.clear_report_generating(telegram_id, "date_calendar")
        await thinking_msg.delete()

        month_names_ru = [
            "",
            "Январь",
            "Февраль",
            "Март",
            "Апрель",
            "Май",
            "Июнь",
            "Июль",
            "Август",
            "Сентябрь",
            "Октябрь",
            "Ноябрь",
            "Декабрь",
        ]
        month_names_en = [
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        month_name = month_names_ru[month] if lang == "ru" else month_names_en[month]
        title = f"Календарь на {month_name} {year}" if lang == "ru" else f"Calendar for {month_name} {year}"
        done_text = (
            f"✨ *{title}* готов!\n\nНажми кнопку ниже, чтобы открыть отчёт."
            if lang == "ru"
            else f"✨ *{title}* is ready!\n\nTap the button below to view your report."
        )
        await callback.message.answer(
            done_text,
            parse_mode="Markdown",
            reply_markup=get_report_view_keyboard("date_calendar", lang, instance_id),
        )
    else:
        info = REPORT_INFO["date_calendar"]
        name = info["name_ru"] if lang == "ru" else info["name_en"]
        desc = f"Премиум отчёт: {name}" if lang == "ru" else f"Premium report: {name}"

        await bot.send_invoice(
            chat_id=telegram_id,
            title=name,
            description=desc,
            payload="report_date_calendar",
            currency="XTR",
            prices=[LabeledPrice(label=name, amount=info["price"])],
        )

    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Show help message."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)
    lang = user.language.value if user else "ru"

    await message.answer(get_text("help", lang), parse_mode="Markdown")


@router.callback_query(F.data == "menu")
async def callback_menu(callback: CallbackQuery):
    """Return to main menu."""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    lang = user.language.value if user else "ru"

    await callback.message.edit_reply_markup(reply_markup=get_main_keyboard(lang))
    await callback.answer()


# Default message handler - questions to AI
@router.message(F.text, StateFilter(None))
async def handle_question(message: Message, state: FSMContext):
    """Handle user questions."""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await message.answer("Please start with /start first")
        return

    lang = user.language.value

    # Check question limit
    if not user.can_ask_question():
        await message.answer(
            get_text("question_limit", lang),
            reply_markup=get_buy_keyboard(lang),
        )
        return

    # Increment question counter
    user = await db.increment_questions_today(user)

    # Save user message
    await db.save_message(telegram_id, "user", message.text)

    thinking_msg = await message.answer(get_text("thinking", lang))

    # Get conversation history
    history = await db.get_conversation_history(telegram_id)

    # Generate response
    profile = get_full_profile(user.name, user.birth_date)
    response = await ai_service.answer_question(user, profile, message.text, history)

    # Save assistant message
    await db.save_message(telegram_id, "assistant", response)

    await thinking_msg.delete()

    # Show remaining questions for free users
    if not user.is_premium():
        remaining = settings.free_questions_per_day - user.questions_today + user.questions_bonus
        footer = f"\n\n_{get_text('question_remaining', lang, count=max(0, remaining))}_"
        response += footer

    await message.answer(response, parse_mode="Markdown")


# Utility functions


def parse_date(text: str) -> Optional[date]:
    """Parse date from various formats."""
    text = text.strip()

    # Try common formats
    formats = ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


# Create dispatcher and bot
def create_bot() -> tuple[Bot, Dispatcher]:
    """Create bot and dispatcher instances."""
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp
