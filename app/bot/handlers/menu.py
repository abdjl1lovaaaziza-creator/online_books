from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states.search import SearchState
from app.bot.keyboards.inline import (
    get_language_keyboard,
    get_categories_keyboard,
    get_textbooks_keyboard,
    get_search_options_keyboard,
    get_search_results_keyboard,
    get_admin_keyboard
)
from app.database.repositories.category import CategoryRepository
from app.database.repositories.book import BookRepository
from app.services.search import search_service
from app.services.user import user_service
from app.services.cache import cache

router = Router(name="menu")


@router.message(
    F.text.in_({"📚 Найти книгу", "📚 Search Books", "🔍 Поиск книг", "🔍 Search Books"})
    | F.text.startswith("📚 Найти")
    | F.text.startswith("🔍")
)
async def menu_search(message: Message, state: FSMContext, user_lang, t):
    """Trigger search prompt with specialized criteria buttons."""
    await state.set_state(SearchState.waiting_for_query)
    kb = get_search_options_keyboard(user_lang=user_lang)
    await message.answer(t("search.prompt"), reply_markup=kb, parse_mode="HTML")


@router.message(
    F.text.in_({"🎓 Учебники", "🎓 Textbooks"})
    | F.text.startswith("🎓")
)
async def menu_textbooks(message: Message, user_lang, t):
    """List educational and textbook disciplines/subjects."""
    kb = get_textbooks_keyboard(user_lang=user_lang)
    title = t("textbooks.title") if "textbooks.title" != t("textbooks.title") else "🎓 <b>Учебники и образовательная литература</b>\n\nВыберите интересующий предмет или дисциплину:"
    await message.answer(title, reply_markup=kb, parse_mode="HTML")


@router.message(
    F.text.in_({"📂 Категории", "📂 Categories", "📚 Категории"})
    | F.text.startswith("📂")
)
async def menu_categories(message: Message, session: AsyncSession, user_lang, t):
    """List general categories and genres."""
    cat_repo = CategoryRepository(session)
    categories = await cat_repo.get_all(is_textbook=False)
    kb = get_categories_keyboard(categories, user_lang=user_lang)
    await message.answer(t("categories.title"), reply_markup=kb, parse_mode="HTML")


@router.message(
    F.text.in_({"🔥 Популярные книги", "🔥 Popular Books"})
    | F.text.startswith("🔥")
)
async def menu_popular(message: Message, session: AsyncSession, user_lang, t):
    """View popular books (automatically discovers books if DB is empty)."""
    book_repo = BookRepository(session)
    books, total = await book_repo.get_popular(limit=5, offset=0)

    if not books:
        # Dynamically populate with classics/popular literature via Google Books & Open Library
        status_msg = await message.answer("🔎 Загружаем популярные книги из библиотеки...", parse_mode="HTML")
        books, total = await search_service.search(
            session=session,
            query="классическая литература шедевры",
            language=user_lang,
            limit=5,
            offset=0
        )
        if not books:
            await status_msg.edit_text("📚 В библиотеке пока нет книг. Воспользуйтесь 📚 <b>Найти книгу</b> для поиска!", parse_mode="HTML")
            return
        await status_msg.delete()

    total_pages = max(1, (total + 4) // 5)
    kb = get_search_results_keyboard(books, page=1, total_pages=total_pages, query="", action_prefix="popular")
    header = f"🔥 <b>Популярные книги</b> (Всего: {total}):"
    await message.answer(header, reply_markup=kb, parse_mode="HTML")


@router.message(
    F.text.in_({"ℹ️ О боте", "ℹ️ About Bot", "ℹ️ О проекте", "ℹ️ About"})
    | F.text.startswith("ℹ️")
)
async def menu_about(message: Message, t):
    """View about Smart Library information."""
    await message.answer(t("about.text"), parse_mode="HTML")


@router.message(F.text.startswith("🌍"))
async def menu_languages(message: Message, t):
    """Open language selector."""
    await message.answer(t("select_language"), reply_markup=get_language_keyboard())


@router.message(F.text.startswith("⚙️"))
async def menu_settings(message: Message, session: AsyncSession, t):
    """View user settings and statistics."""
    stats = await user_service.get_stats(session, message.from_user.id)
    text = t(
        "settings.title",
        user_id=stats.get("user_id", message.from_user.id),
        language=stats.get("language", "en").upper(),
        registered_date=stats.get("registered_date", "Today"),
        favorites_count=stats.get("favorites_count", 0),
        downloads_count=stats.get("downloads_count", 0)
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("settings.change_lang"), callback_data="open_lang")]
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "open_lang")
async def callback_open_lang(callback, t):
    await callback.message.edit_text(t("select_language"), reply_markup=get_language_keyboard())
    await callback.answer()


@router.message(F.text.startswith("⚡"))
async def menu_admin_shortcut(message: Message, session: AsyncSession, user, t):
    """Admin menu entry point."""
    if not user or not user.is_admin:
        await message.answer(t("errors.unauthorized"))
        return

    from app.database.repositories.user import UserRepository
    from app.database.repositories.download import DownloadRepository

    user_repo = UserRepository(session)
    book_repo = BookRepository(session)
    dl_repo = DownloadRepository(session)

    total_users = await user_repo.count_total_users()
    active_users = await user_repo.count_active_users()
    total_books = await book_repo.count_total_books()
    total_dls = await dl_repo.count_total_downloads()

    stats_text = t(
        "admin.stats",
        total_users=total_users,
        active_users=active_users,
        total_books=total_books,
        total_downloads=total_dls,
        redis_status=cache.status_str
    )

    await message.answer(
        f"{t('admin.title')}\n\n{stats_text}",
        reply_markup=get_admin_keyboard(t),
        parse_mode="HTML"
    )
