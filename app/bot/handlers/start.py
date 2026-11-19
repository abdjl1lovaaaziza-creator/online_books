from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.reply import get_main_menu_keyboard
from app.bot.keyboards.inline import get_language_keyboard
from app.services.user import user_service

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext, session: AsyncSession, user, t, user_lang):
    """Handle /start command."""
    await state.clear()
    is_admin = bool(user and user.is_admin)

    # Send welcome text
    first_name = message.from_user.first_name if message.from_user and message.from_user.first_name else ""
    user_name = first_name or (message.from_user.username if message.from_user else "") or "друг"
    welcome_text = t("welcome", name=user_name)
    menu_kb = get_main_menu_keyboard(t, is_admin=is_admin)

    await message.answer(
        text=welcome_text,
        reply_markup=menu_kb,
        parse_mode="HTML"
    )


@router.message(Command("language"))
async def handle_language_command(message: Message, t):
    """Handle /language command."""
    prompt = t("select_language")
    await message.answer(
        text=prompt,
        reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("lang:"))
async def handle_language_selection(callback: CallbackQuery, session: AsyncSession, t, user):
    """Handle language selection callback."""
    lang_code = callback.data.split(":")[1]
    success = await user_service.change_language(session, callback.from_user.id, lang_code)
    await session.commit()

    lang_names = {
        "en": "English 🇬🇧",
        "ru": "Русский 🇷🇺",
        "uz": "O'zbekcha 🇺🇿",
        "tr": "Türkçe 🇹🇷",
        "ar": "العربية 🇸🇦",
        "de": "Deutsch 🇩🇪",
        "fr": "Français 🇫🇷",
        "es": "Español 🇪🇸"
    }
    lang_name = lang_names.get(lang_code, lang_code)

    # Localize with new language
    from app.localization.manager import i18n
    new_t = lambda key, **kwargs: i18n.get(key, lang=lang_code, **kwargs)

    confirm_msg = new_t("language_changed", lang_name=lang_name)
    is_admin = bool(user and user.is_admin)
    new_menu = get_main_menu_keyboard(new_t, is_admin=is_admin)

    await callback.message.delete()
    await callback.message.answer(confirm_msg, reply_markup=new_menu, parse_mode="HTML")
    await callback.answer()
