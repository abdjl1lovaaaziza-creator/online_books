from typing import List, Tuple
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.favorite import Favorite
from app.database.models.book import Book


class FavoriteRepository:
    """Repository for user favorites operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_favorite(self, user_id: int, book_id: int) -> bool:
        """Add book to user's favorites if not already present."""
        if await self.is_favorite(user_id, book_id):
            return False

        fav = Favorite(user_id=user_id, book_id=book_id)
        self.session.add(fav)
        await self.session.flush()
        return True

    async def remove_favorite(self, user_id: int, book_id: int) -> bool:
        """Remove book from user's favorites."""
        stmt = delete(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.book_id == book_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def is_favorite(self, user_id: int, book_id: int) -> bool:
        """Check if book is favorited by user."""
        stmt = select(func.count(Favorite.id)).where(
            Favorite.user_id == user_id,
            Favorite.book_id == book_id
        )
        count = (await self.session.execute(stmt)).scalar() or 0
        return count > 0

    async def get_user_favorites(self, user_id: int, limit: int = 10, offset: int = 0) -> Tuple[List[Book], int]:
        """Fetch user's favorite books with pagination."""
        count_stmt = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(Book)
            .join(Favorite, Favorite.book_id == Book.id)
            .options(
                selectinload(Book.authors),
                selectinload(Book.categories),
                selectinload(Book.formats)
            )
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_user_favorites(self, user_id: int) -> int:
        """Count total favorites for user."""
        stmt = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
