from typing import List, Tuple, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.download import Download
from app.database.models.book import Book


class DownloadRepository:
    """Repository for download statistics and user history."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_download(
        self,
        user_id: int,
        book_id: int,
        file_format: str,
        telegram_file_id: Optional[str] = None
    ) -> Download:
        """Log a book download event."""
        dl = Download(
            user_id=user_id,
            book_id=book_id,
            format=file_format,
            telegram_file_id=telegram_file_id
        )
        self.session.add(dl)
        await self.session.flush()
        return dl

    async def get_user_downloads(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Download], int]:
        """Get paginated list of books downloaded by user."""
        count_stmt = select(func.count(Download.id)).where(Download.user_id == user_id)
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(Download)
            .options(
                selectinload(Download.book).selectinload(Book.authors),
                selectinload(Download.book).selectinload(Book.formats)
            )
            .where(Download.user_id == user_id)
            .order_by(Download.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_total_downloads(self) -> int:
        """Count total downloads recorded across system."""
        stmt = select(func.count(Download.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_user_downloads(self, user_id: int) -> int:
        """Count downloads by specific user."""
        stmt = select(func.count(Download.id)).where(Download.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
