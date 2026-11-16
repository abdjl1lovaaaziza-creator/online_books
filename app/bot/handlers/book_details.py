from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.repositories.book import BookRepository
from app.database.repositories.favorite import FavoriteRepository
from app.bot.keyboards.inline import get_book_details_keyboard
from app.services.download import download_service
from app.utils.formatting import format_book_caption_html

router = Router(name="book_details")


@router.callback_query(F.data.startswith("book:"))
async def view_book_details(callback: CallbackQuery, session: AsyncSession, user, user_lang, t):
    """Render full book details view."""
    parts = callback.data.split(":")
    book_id = int(parts[1])
    back_action = parts[2] if len(parts) > 2 else None
    back_page = int(parts[3]) if len(parts) > 3 else 1
    back_query = parts[4] if len(parts) > 4 else ""

    book_repo = BookRepository(session)
    book = await book_repo.get_by_id(book_id)
    if not book:
        await callback.answer("Book not found or removed.", show_alert=True)
        return

    # Increment view count
    await book_repo.increment_views(book.id)
    await session.commit()

    fav_repo = FavoriteRepository(session)
    is_fav = await fav_repo.is_favorite(user.id, book.id) if user else False

    caption = format_book_caption_html(book, user_lang)
    kb = get_book_details_keyboard(
        book=book,
        is_favorite=is_fav,
        t=t,
        back_action=back_action,
        back_page=back_page,
        back_query=back_query
    )

    try:
        if book.cover_url and book.cover_url.startswith(("http://", "https://")):
            # Send cover image
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=book.cover_url,
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(caption, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Error rendering book view with photo: {e}. Falling back to text message.")
        await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data.startswith("fav_toggle:"))
async def toggle_favorite(callback: CallbackQuery, session: AsyncSession, user, t):
    """Toggle book in user favorites."""
    if not user:
        await callback.answer(t("errors.unauthorized"), show_alert=True)
        return

    book_id = int(callback.data.split(":")[1])
    book_repo = BookRepository(session)
    book = await book_repo.get_by_id(book_id)
    if not book:
        await callback.answer("Book not found.", show_alert=True)
        return

    fav_repo = FavoriteRepository(session)
    is_fav = await fav_repo.is_favorite(user.id, book.id)

    if is_fav:
        await fav_repo.remove_favorite(user.id, book.id)
        alert_text = t("book.fav_removed", title=book.title[:30])
        new_fav_state = False
    else:
        await fav_repo.add_favorite(user.id, book.id)
        alert_text = t("book.fav_added", title=book.title[:30])
        new_fav_state = True

    await session.commit()

    # Rebuild keyboard with updated favorite button
    kb = get_book_details_keyboard(
        book=book,
        is_favorite=new_fav_state,
        t=t
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass

    await callback.answer(alert_text, show_alert=True)


@router.callback_query(F.data.startswith("dl:"))
async def handle_book_download(callback: CallbackQuery, bot: Bot, session: AsyncSession, user, t):
    """Handle book file download and delivery."""
    parts = callback.data.split(":")
    book_id = int(parts[1])
    format_id = int(parts[2])

    book_repo = BookRepository(session)
    book = await book_repo.get_by_id(book_id)
    if not book:
        await callback.answer("Book not found.", show_alert=True)
        return

    format_obj = next((f for f in book.formats if f.id == format_id), None)
    if not format_obj:
        await callback.answer("Requested file format is unavailable.", show_alert=True)
        return

    # Inform user download preparation started
    await callback.answer(t("download.preparing", title=book.title[:25], format=format_obj.format.upper()))
    status_msg = await callback.message.answer(
        t("download.downloading"),
        parse_mode="HTML"
    )

    success, file_id, error_reason = await download_service.deliver_file(
        bot=bot,
        chat_id=callback.message.chat.id,
        user_id=user.id,
        book=book,
        format_obj=format_obj,
        session=session
    )

    await status_msg.delete()

    if success:
        return

    # Handle errors gracefully
    if error_reason and error_reason.startswith("too_large:"):
        size_str = error_reason.split(":")[1]
        link = book.access_url or format_obj.file_url
        await callback.message.answer(
            t("download.too_large", size=size_str, link=link),
            parse_mode="HTML"
        )
    else:
        link = book.access_url or format_obj.file_url
        await callback.message.answer(
            t("download.failed", link=link),
            parse_mode="HTML"
        )
