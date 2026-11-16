import math
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.bot.states.search import SearchState
from app.bot.keyboards.inline import get_search_results_keyboard
from app.services.search import search_service
from app.database.repositories.search_history import SearchHistoryRepository
from app.database.repositories.book import BookRepository
from app.database.repositories.category import CategoryRepository
from app.utils.formatting import escape_html

router = Router(name="search")


@router.callback_query(F.data.startswith("search_mode:"))
async def handle_search_mode_selection(callback: CallbackQuery, state: FSMContext, user_lang, t):
    """Handle user selection of dedicated search criteria."""
    mode = callback.data.split(":")[1]

    if mode == "title":
        await state.set_state(SearchState.waiting_for_title)
        prompt = t("search.prompt_title") if "search.prompt_title" != t("search.prompt_title") else "📖 <b>Поиск по названию</b>\n\nОтправьте название книги или пособия:"
    elif mode == "author":
        await state.set_state(SearchState.waiting_for_author)
        prompt = t("search.prompt_author") if "search.prompt_author" != t("search.prompt_author") else "✍️ <b>Поиск по автору</b>\n\nОтправьте имя или фамилию автора:"
    elif mode == "keywords":
        await state.set_state(SearchState.waiting_for_keywords)
        prompt = t("search.prompt_keywords") if "search.prompt_keywords" != t("search.prompt_keywords") else "🏷️ <b>Поиск по ключевым словам</b>\n\nОтправьте ключевые слова или тему:"
    elif mode == "textbook":
        await state.set_state(SearchState.waiting_for_textbook_subject)
        prompt = t("search.prompt_textbook") if "search.prompt_textbook" != t("search.prompt_textbook") else "🎓 <b>Поиск учебников по предмету</b>\n\nВведите предмет или учебную дисциплину:"
    else:
        await state.set_state(SearchState.waiting_for_query)
        prompt = t("search.prompt")

    await callback.message.edit_text(prompt, parse_mode="HTML")
    await callback.answer()


@router.message(SearchState.waiting_for_title)
async def process_title_search(message: Message, state: FSMContext, session: AsyncSession, user, user_lang, t):
    """Handle search specifically by title."""
    query = message.text.strip()
    await state.clear()
    await _execute_search(message, session, user, user_lang, t, query=query, search_query=f"intitle:{query}")


@router.message(SearchState.waiting_for_author)
async def process_author_search(message: Message, state: FSMContext, session: AsyncSession, user, user_lang, t):
    """Handle search specifically by author."""
    query = message.text.strip()
    await state.clear()
    await _execute_search(message, session, user, user_lang, t, query=query, search_query=f"inauthor:{query}")


@router.message(SearchState.waiting_for_keywords)
async def process_keywords_search(message: Message, state: FSMContext, session: AsyncSession, user, user_lang, t):
    """Handle search specifically by keywords."""
    query = message.text.strip()
    await state.clear()
    await _execute_search(message, session, user, user_lang, t, query=query, search_query=query)


@router.message(SearchState.waiting_for_textbook_subject)
async def process_textbook_subject_search(message: Message, state: FSMContext, session: AsyncSession, user, user_lang, t):
    """Handle search specifically for textbooks by subject."""
    query = message.text.strip()
    await state.clear()
    await _execute_search(
        message,
        session,
        user,
        user_lang,
        t,
        query=f"🎓 {query}",
        search_query=f"учебник {query} textbook",
        is_textbook=True
    )


@router.message(SearchState.waiting_for_query)
@router.message(
    F.text
    & ~F.text.startswith(("/", "🔍", "📚", "🎓", "🌍", "🔥", "🆕", "⭐", "📖", "⚙️", "ℹ️", "⚡", "📂"))
)
async def process_general_search_query(message: Message, state: FSMContext, session: AsyncSession, user, user_lang, t):
    """Process incoming general search query text."""
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Пожалуйста, введите как минимум 2 символа для поиска.")
        return

    await state.clear()
    await _execute_search(message, session, user, user_lang, t, query=query, search_query=query)


async def _execute_search(
    message: Message,
    session: AsyncSession,
    user,
    user_lang: str,
    t,
    query: str,
    search_query: str,
    is_textbook: bool = None
):
    """Unified internal search executor."""
    status_msg = await message.answer(t("search.searching", query=escape_html(query)), parse_mode="HTML")

    try:
        page_size = 5
        books, total_count = await search_service.search(
            session=session,
            query=search_query,
            language=user_lang,
            is_textbook=is_textbook,
            limit=page_size,
            offset=0
        )

        # Record history
        if user:
            hist_repo = SearchHistoryRepository(session)
            await hist_repo.record_search(
                user_id=user.id,
                query=query,
                result_count=total_count
            )
            await session.commit()

        if not books:
            await status_msg.edit_text(t("search.no_results", query=escape_html(query)), parse_mode="HTML")
            return

        total_pages = max(1, math.ceil(total_count / page_size))
        kb = get_search_results_keyboard(
            books=books,
            page=1,
            total_pages=total_pages,
            query=query[:15],
            action_prefix="search"
        )
        header = t("search.results_header", query=escape_html(query), page=1, total_pages=total_pages, count=total_count)
        await status_msg.edit_text(header, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error handling search for '{query}': {e}")
        await status_msg.edit_text(t("errors.general"), parse_mode="HTML")


@router.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery, session: AsyncSession, user_lang, t):
    """Handle pagination across all search and browsing lists."""
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return

    action_prefix = parts[1]
    page = int(parts[2])
    query = parts[3]
    page_size = 5
    offset = (page - 1) * page_size

    book_repo = BookRepository(session)

    if action_prefix == "search":
        books, total_count = await search_service.search(
            session=session,
            query=query,
            language=user_lang,
            limit=page_size,
            offset=offset
        )
        total_pages = max(1, math.ceil(total_count / page_size))
        kb = get_search_results_keyboard(books, page=page, total_pages=total_pages, query=query, action_prefix="search")
        header = t("search.results_header", query=escape_html(query), page=page, total_pages=total_pages, count=total_count)
        await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")

    elif action_prefix == "popular":
        books, total_count = await book_repo.get_popular(limit=page_size, offset=offset)
        total_pages = max(1, math.ceil(total_count / page_size))
        kb = get_search_results_keyboard(books, page=page, total_pages=total_pages, query="", action_prefix="popular")
        header = f"🔥 <b>Популярные книги</b> (Стр. {page}/{total_pages}):"
        await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")

    elif action_prefix == "recent":
        books, total_count = await book_repo.get_recently_added(limit=page_size, offset=offset)
        total_pages = max(1, math.ceil(total_count / page_size))
        kb = get_search_results_keyboard(books, page=page, total_pages=total_pages, query="", action_prefix="recent")
        header = f"🆕 <b>Недавно добавленные книги</b> (Стр. {page}/{total_pages}):"
        await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")

    elif action_prefix == "cat":
        cat_id = int(query)
        cat_repo = CategoryRepository(session)
        category = await cat_repo.get_by_id(cat_id)
        cat_name = category.get_name(user_lang) if category else "Категория"

        books, total_count = await book_repo.search(
            category_id=cat_id,
            limit=page_size,
            offset=offset
        )
        total_pages = max(1, math.ceil(total_count / page_size))
        kb = get_search_results_keyboard(books, page=page, total_pages=total_pages, query=str(cat_id), action_prefix="cat")
        header = t("categories.category_books", category=cat_name, page=page, total_pages=total_pages)
        await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")

    elif action_prefix == "tb":
        # Textbook subject pagination
        books, total_count = await search_service.search(
            session=session,
            query=f"учебник {query} textbook",
            language=user_lang,
            is_textbook=True,
            limit=page_size,
            offset=offset
        )
        total_pages = max(1, math.ceil(total_count / page_size))
        kb = get_search_results_keyboard(books, page=page, total_pages=total_pages, query=query, action_prefix="tb")
        header = f"🎓 <b>Учебники: {query.capitalize()}</b> (Стр. {page}/{total_pages}):"
        await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()
