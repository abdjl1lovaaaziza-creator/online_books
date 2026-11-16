import math
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.favorite import FavoriteRepository
from app.bot.keyboards.inline import get_search_results_keyboard

router = Router(name="favorites")


@router.message(F.text.startswith("⭐"))
async def view_favorites(message: Message, session: AsyncSession, user, t):
    """View user favorites list."""
    if not user:
        await message.answer(t("errors.unauthorized"))
        return

    fav_repo = FavoriteRepository(session)
    page_size = 5
    books, total = await fav_repo.get_user_favorites(user.id, limit=page_size, offset=0)

    if not books:
        await message.answer(t("favorites.empty"), parse_mode="HTML")
        return

    total_pages = max(1, math.ceil(total / page_size))
    kb = get_search_results_keyboard(
        books=books,
        page=1,
        total_pages=total_pages,
        query="",
        action_prefix="fav"
    )
    header = t("favorites.header", total=total, page=1, total_pages=total_pages)
    await message.answer(header, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("page:fav:"))
async def paginate_favorites(callback: CallbackQuery, session: AsyncSession, user, t):
    """Paginate user favorites."""
    if not user:
        await callback.answer()
        return

    parts = callback.data.split(":")
    page = int(parts[2])
    page_size = 5
    offset = (page - 1) * page_size

    fav_repo = FavoriteRepository(session)
    books, total = await fav_repo.get_user_favorites(user.id, limit=page_size, offset=offset)
    total_pages = max(1, math.ceil(total / page_size))

    kb = get_search_results_keyboard(
        books=books,
        page=page,
        total_pages=total_pages,
        query="",
        action_prefix="fav"
    )
    header = t("favorites.header", total=total, page=page, total_pages=total_pages)
    await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
