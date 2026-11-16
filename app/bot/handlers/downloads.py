import math
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.download import DownloadRepository

router = Router(name="downloads")


@router.message(F.text.startswith("📖"))
async def view_download_history(message: Message, session: AsyncSession, user, t):
    """View user download history."""
    if not user:
        await message.answer(t("errors.unauthorized"))
        return

    dl_repo = DownloadRepository(session)
    downloads, total = await dl_repo.get_user_downloads(user.id, limit=10, offset=0)

    if not downloads:
        await message.answer(t("downloads_history.empty"), parse_mode="HTML")
        return

    lines = [t("downloads_history.header", total=total, page=1, total_pages=max(1, math.ceil(total / 10)))]
    lines.append("")
    for i, dl in enumerate(downloads, 1):
        book_title = dl.book.title if dl.book else "Unknown Book"
        lines.append(f"{i}. 📖 <b>{book_title}</b> ({dl.format.upper()}) - <i>{dl.created_at.strftime('%Y-%m-%d')}</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")
