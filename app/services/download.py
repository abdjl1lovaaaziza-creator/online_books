import io
import re
from typing import Optional, Tuple
import httpx
from aiogram import Bot
from aiogram.types import BufferedInputFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models.book import Book
from app.database.models.format import BookFormat
from app.database.repositories.book import BookRepository
from app.database.repositories.download import DownloadRepository


class DownloadService:
    """Manages secure file delivery, caching, and Telegram size handling."""

    ALLOWED_FORMATS = {"pdf", "epub", "fb2", "djvu", "txt", "mobi", "docx"}
    MAX_BYTES = settings.MAX_DOWNLOAD_SIZE_MB * 1024 * 1024

    @staticmethod
    def sanitize_filename(name: str, ext: str) -> str:
        """Create a safe filename for Telegram documents."""
        clean = re.sub(r'[\\/*?:"<>|]', "", name)
        clean = clean.replace(" ", "_").strip()[:80]
        return f"{clean or 'document'}.{ext.lower()}"

    async def deliver_file(
        self,
        bot: Bot,
        chat_id: int,
        user_id: int,
        book: Book,
        format_obj: BookFormat,
        session: AsyncSession
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Deliver book file to user:
        1. If telegram_file_id is cached, instantly send using file_id.
        2. Otherwise, check file size via HEAD request.
        3. If file exceeds 50MB, return official link (Telegram limit).
        4. Stream and buffer file, send via Telegram, record file_id in DB.
        5. Track download statistics.

        Returns: (success, telegram_file_id_or_none, error_reason_or_none)
        """
        book_repo = BookRepository(session)
        download_repo = DownloadRepository(session)

        # 1. Cached Telegram file_id fast path
        if format_obj.telegram_file_id:
            try:
                caption = f"📖 <b>{book.title}</b> ({format_obj.format.upper()})"
                await bot.send_document(
                    chat_id=chat_id,
                    document=format_obj.telegram_file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
                await download_repo.record_download(
                    user_id=user_id,
                    book_id=book.id,
                    file_format=format_obj.format,
                    telegram_file_id=format_obj.telegram_file_id
                )
                await book_repo.increment_downloads(book.id)
                await session.commit()
                return True, format_obj.telegram_file_id, None
            except Exception as e:
                logger.warning(f"Failed sending cached file_id {format_obj.telegram_file_id}: {e}. Retrying download.")

        # 2. Check if direct download or official access link
        if not format_obj.is_direct_download or not format_obj.file_url.startswith(("http://", "https://")):
            return False, None, "not_direct_link"

        # 3. Size check and download stream
        try:
            async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
                # First attempt HEAD to check content-length
                try:
                    head_res = await client.head(format_obj.file_url)
                    cl = head_res.headers.get("content-length")
                    if cl and cl.isdigit() and int(cl) > self.MAX_BYTES:
                        size_mb = f"{int(cl) / (1024 * 1024):.1f} MB"
                        return False, None, f"too_large:{size_mb}"
                except Exception:
                    pass

                # Stream response
                async with client.stream("GET", format_obj.file_url) as res:
                    if res.status_code != 200:
                        return False, None, "http_error"

                    content_length = res.headers.get("content-length")
                    if content_length and int(content_length) > self.MAX_BYTES:
                        size_mb = f"{int(content_length) / (1024 * 1024):.1f} MB"
                        return False, None, f"too_large:{size_mb}"

                    buffer = io.BytesIO()
                    downloaded = 0
                    async for chunk in res.aiter_bytes(chunk_size=65536):
                        downloaded += len(chunk)
                        if downloaded > self.MAX_BYTES:
                            size_mb = f"{downloaded / (1024 * 1024):.1f} MB"
                            return False, None, f"too_large:{size_mb}"
                        buffer.write(chunk)

                    buffer.seek(0)
                    filename = self.sanitize_filename(book.title, format_obj.format)
                    input_file = BufferedInputFile(buffer.getvalue(), filename=filename)

                    caption = f"📖 <b>{book.title}</b> ({format_obj.format.upper()})"
                    msg = await bot.send_document(
                        chat_id=chat_id,
                        document=input_file,
                        caption=caption,
                        parse_mode="HTML"
                    )

                    new_file_id = msg.document.file_id if msg.document else None
                    if new_file_id:
                        await book_repo.update_format_telegram_file_id(format_obj.id, new_file_id)

                    await download_repo.record_download(
                        user_id=user_id,
                        book_id=book.id,
                        file_format=format_obj.format,
                        telegram_file_id=new_file_id
                    )
                    await book_repo.increment_downloads(book.id)
                    await session.commit()

                    return True, new_file_id, None

        except Exception as e:
            logger.error(f"Error downloading/transmitting file for book {book.id}: {e}")
            return False, None, str(e)


download_service = DownloadService()
