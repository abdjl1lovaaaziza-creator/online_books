import math
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.repositories.category import CategoryRepository
from app.database.repositories.book import BookRepository
from app.services.search import search_service
from app.bot.states.search import SearchState
from app.bot.keyboards.inline import get_search_results_keyboard

router = Router(name="categories")

SUBJECT_MAPPING = {
    "math": ("Высшая математика и алгебра", "mathematics algebra textbook"),
    "physics": ("Физика", "physics textbook"),
    "cs": ("Информатика и программирование", "computer science algorithms python programming textbook"),
    "chemistry": ("Химия", "chemistry textbook"),
    "biology": ("Биология и экология", "biology textbook"),
    "history": ("Всемирная история", "history textbook"),
    "economics": ("Экономика и финансы", "economics finance business textbook"),
    "languages": ("Иностранные языки", "english foreign languages textbook"),
    "medicine": ("Медицина и анатомия", "medicine anatomy textbook"),
    "law": ("Право и юриспруденция", "law jurisprudence textbook"),
    "school": ("Школьная программа", "school textbook учебник 10 11 класс"),
    "university": ("Университетские учебники", "university higher education textbook"),
}


@router.callback_query(F.data.startswith("tb:"))
async def handle_textbook_subject_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user_lang, t):
    """Handle click on textbook subject button."""
    subj_code = callback.data.split(":")[1]

    if subj_code == "custom":
        await state.set_state(SearchState.waiting_for_textbook_subject)
        prompt = (
            "🎓 <b>Поиск учебников по предмету</b>\n\n"
            "Введите название учебной дисциплины или предмета (например: <i>Сопротивление материалов</i>, <i>Биохимия</i>, <i>Микроэкономика</i>):"
        )
        await callback.message.edit_text(prompt, parse_mode="HTML")
        await callback.answer()
        return

    subj_info = SUBJECT_MAPPING.get(subj_code, (subj_code.capitalize(), f"{subj_code} textbook"))
    subj_name, search_term = subj_info

    await callback.message.edit_text(f"🔎 Подбираем учебники по предмету: <b>{subj_name}</b>...", parse_mode="HTML")

    page_size = 5
    books, total_count = await search_service.search(
        session=session,
        query=f"учебник {search_term}",
        language=None,
        is_textbook=True,
        limit=page_size,
        offset=0
    )

    if not books:
        await callback.message.edit_text(
            f"🎓 <b>{subj_name}</b>\n\nК сожалению, учебников по данному предмету пока не найдено. Попробуйте поиск через 📚 <b>Найти книгу</b>.",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    total_pages = max(1, math.ceil(total_count / page_size))
    kb = get_search_results_keyboard(
        books=books,
        page=1,
        total_pages=total_pages,
        query=subj_code,
        action_prefix="tb"
    )

    header = f"🎓 <b>Учебники: {subj_name}</b> (Стр. 1/{total_pages}):\nНайдено {total_count} учебных изданий:"
    await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def handle_category_click(callback: CallbackQuery, session: AsyncSession, user_lang, t):
    """Handle click on category button to list books in that category."""
    parts = callback.data.split(":")
    cat_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 1

    cat_repo = CategoryRepository(session)
    category = await cat_repo.get_by_id(cat_id)
    if not category:
        await callback.answer("Категория не найдена.", show_alert=True)
        return

    book_repo = BookRepository(session)
    page_size = 5
    offset = (page - 1) * page_size

    cat_name = category.get_name(user_lang)

    books, total_count = await book_repo.search(
        category_id=cat_id,
        limit=page_size,
        offset=offset
    )

    # Dynamic fallback to Google Books and Open Library if DB has no books yet for this category
    if not books:
        await callback.message.edit_text(f"🔎 Ищем книги в категории <b>{category.icon} {cat_name}</b>...", parse_mode="HTML")
        books, total_count = await search_service.search(
            session=session,
            query=category.name_ru or category.name_en or cat_name,
            language=None,
            is_textbook=category.is_textbook,
            limit=page_size,
            offset=offset
        )

    if not books:
        await callback.message.edit_text(
            f"📂 <b>{category.icon} {cat_name}</b>\n\nВ данной категории пока нет книг. Воспользуйтесь 📚 <b>Найти книгу</b> для расширенного поиска!",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    total_pages = max(1, math.ceil(total_count / page_size))
    kb = get_search_results_keyboard(
        books=books,
        page=page,
        total_pages=total_pages,
        query=str(cat_id),
        action_prefix="cat"
    )

    header = t(
        "categories.category_books",
        category=f"{category.icon} {cat_name}",
        page=page,
        total_pages=total_pages
    )
    await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
