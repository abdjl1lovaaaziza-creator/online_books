from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.category import Category


class CategoryRepository:
    """Repository for category queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, is_textbook: Optional[bool] = None, only_active: bool = True) -> List[Category]:
        """Fetch categories, optionally filtered by textbook flag and active status."""
        stmt = select(Category)
        if only_active:
            stmt = stmt.where(Category.is_active == True)  # noqa: E712
        if is_textbook is not None:
            stmt = stmt.where(Category.is_textbook == is_textbook)
        stmt = stmt.order_by(Category.name_en.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """Fetch category by slug."""
        stmt = select(Category).where(Category.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        """Fetch category by id."""
        stmt = select(Category).where(Category.id == category_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        slug: str,
        name_en: str,
        name_ru: str,
        name_uz: str,
        name_tr: str,
        name_ar: str,
        name_de: str,
        name_fr: str,
        name_es: str,
        icon: str = "📚",
        is_textbook: bool = False
    ) -> Category:
        """Create a new category."""
        category = Category(
            slug=slug,
            name_en=name_en,
            name_ru=name_ru,
            name_uz=name_uz,
            name_tr=name_tr,
            name_ar=name_ar,
            name_de=name_de,
            name_fr=name_fr,
            name_es=name_es,
            icon=icon,
            is_textbook=is_textbook,
            is_active=True
        )
        self.session.add(category)
        await self.session.flush()
        return category
