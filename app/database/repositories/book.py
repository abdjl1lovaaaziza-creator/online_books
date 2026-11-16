from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, update, distinct
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.book import Book, book_categories, book_authors
from app.database.models.author import Author
from app.database.models.category import Category
from app.database.models.format import BookFormat


class BookRepository:
    """Data access repository for books and related entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, book_id: int) -> Optional[Book]:
        """Fetch book with loaded authors, categories, and formats."""
        stmt = (
            select(Book)
            .options(
                selectinload(Book.authors),
                selectinload(Book.categories),
                selectinload(Book.formats)
            )
            .where(Book.id == book_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_source(self, source_name: str, source_id: str) -> Optional[Book]:
        """Find existing book by source identifier."""
        stmt = (
            select(Book)
            .options(
                selectinload(Book.authors),
                selectinload(Book.categories),
                selectinload(Book.formats)
            )
            .where(Book.source_name == source_name, Book.source_id == source_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Find book by ISBN."""
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        stmt = (
            select(Book)
            .options(
                selectinload(Book.authors),
                selectinload(Book.categories),
                selectinload(Book.formats)
            )
            .where(Book.isbn == clean_isbn)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        query: str = "",
        language: Optional[str] = None,
        file_format: Optional[str] = None,
        year: Optional[int] = None,
        category_id: Optional[int] = None,
        is_textbook: Optional[bool] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Book], int]:
        """
        Search books across title, author, description, and ISBN with filters.
        Returns a tuple of (books, total_count).
        """
        base_stmt = select(Book).distinct()

        if category_id:
            base_stmt = base_stmt.join(book_categories).where(book_categories.c.category_id == category_id)

        conditions = []
        if query:
            clean_q = f"%{query.strip().lower()}%"
            author_subq = (
                select(book_authors.c.book_id)
                .join(Author, Author.id == book_authors.c.author_id)
                .where(func.lower(Author.name).like(clean_q))
            )
            conditions.append(
                or_(
                    func.lower(Book.title).like(clean_q),
                    func.lower(Book.description).like(clean_q),
                    Book.isbn.like(clean_q),
                    Book.id.in_(author_subq)
                )
            )

        if language:
            conditions.append(func.lower(Book.language) == language.lower())

        if year:
            conditions.append(Book.publication_year == year)

        if is_textbook is not None:
            conditions.append(Book.is_textbook == is_textbook)

        if file_format:
            format_subq = (
                select(BookFormat.book_id)
                .where(func.lower(BookFormat.format) == file_format.lower())
            )
            conditions.append(Book.id.in_(format_subq))

        if conditions:
            base_stmt = base_stmt.where(*conditions)

        # Count total matches
        count_stmt = select(func.count(distinct(Book.id)))
        if category_id:
            count_stmt = count_stmt.join(book_categories).where(book_categories.c.category_id == category_id)
        if conditions:
            count_stmt = count_stmt.where(*conditions)

        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        # Execute paginated fetch
        data_stmt = (
            base_stmt
            .options(
                selectinload(Book.authors),
                selectinload(Book.categories),
                selectinload(Book.formats)
            )
            .order_by(Book.downloads_count.desc(), Book.views_count.desc(), Book.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(data_stmt)
        books = list(result.scalars().all())
        return books, total_count

    async def get_popular(self, limit: int = 10, offset: int = 0) -> Tuple[List[Book], int]:
        """Fetch popular books ordered by download count and views."""
        count_stmt = select(func.count(Book.id))
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(Book)
            .options(
                selectinload(Book.authors),
                selectinload(Book.categories),
                selectinload(Book.formats)
            )
            .order_by(Book.downloads_count.desc(), Book.views_count.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_recently_added(self, limit: int = 10, offset: int = 0) -> Tuple[List[Book], int]:
        """Fetch recently added books."""
        count_stmt = select(func.count(Book.id))
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(Book)
            .options(
                selectinload(Book.authors),
                selectinload(Book.categories),
                selectinload(Book.formats)
            )
            .order_by(Book.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def increment_views(self, book_id: int) -> None:
        """Increment book view count."""
        stmt = (
            update(Book)
            .where(Book.id == book_id)
            .values(views_count=Book.views_count + 1)
        )
        await self.session.execute(stmt)

    async def increment_downloads(self, book_id: int) -> None:
        """Increment book download counter."""
        stmt = (
            update(Book)
            .where(Book.id == book_id)
            .values(downloads_count=Book.downloads_count + 1)
        )
        await self.session.execute(stmt)

    async def update_format_telegram_file_id(self, format_id: int, telegram_file_id: str) -> None:
        """Cache Telegram file_id for subsequent instant file sending."""
        stmt = (
            update(BookFormat)
            .where(BookFormat.id == format_id)
            .values(telegram_file_id=telegram_file_id)
        )
        await self.session.execute(stmt)

    async def count_total_books(self) -> int:
        """Count total books in catalog."""
        stmt = select(func.count(Book.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def save_or_update(
        self,
        title: str,
        source_name: str,
        source_id: Optional[str] = None,
        original_title: Optional[str] = None,
        description: Optional[str] = None,
        language: str = "en",
        publication_year: Optional[int] = None,
        publisher: Optional[str] = None,
        isbn: Optional[str] = None,
        cover_url: Optional[str] = None,
        access_url: Optional[str] = None,
        license_str: str = "Public Domain / Open Access",
        is_textbook: bool = False,
        authors_names: Optional[List[str]] = None,
        formats_data: Optional[List[dict]] = None
    ) -> Book:
        """Create or update a book entity along with its authors and formats."""
        book: Optional[Book] = None
        if source_id:
            book = await self.get_by_source(source_name, source_id)
        if not book and isbn:
            book = await self.get_by_isbn(isbn)

        # Resolve Authors
        author_objs = []
        if authors_names:
            for author_name in authors_names:
                cleaned_name = author_name.strip()
                if cleaned_name:
                    stmt = select(Author).where(func.lower(Author.name) == cleaned_name.lower())
                    author_obj = (await self.session.execute(stmt)).scalar_one_or_none()
                    if not author_obj:
                        author_obj = Author(name=cleaned_name)
                        self.session.add(author_obj)
                        await self.session.flush()
                    author_objs.append(author_obj)

        if not book:
            format_objs = []
            if formats_data:
                for fmt_item in formats_data:
                    format_objs.append(
                        BookFormat(
                            format=fmt_item["format"].lower(),
                            file_url=fmt_item["file_url"],
                            file_size=fmt_item.get("file_size"),
                            telegram_file_id=fmt_item.get("telegram_file_id"),
                            is_direct_download=fmt_item.get("is_direct_download", True)
                        )
                    )

            book = Book(
                title=title,
                original_title=original_title,
                description=description,
                language=language or "en",
                publication_year=publication_year,
                publisher=publisher,
                isbn=isbn,
                cover_url=cover_url,
                source_name=source_name,
                source_id=source_id,
                access_url=access_url,
                license=license_str,
                is_textbook=is_textbook,
                authors=author_objs,
                formats=format_objs
            )
            self.session.add(book)
            await self.session.flush()
        else:
            # Update fields if new data is richer
            if not book.cover_url and cover_url:
                book.cover_url = cover_url
            if not book.description and description:
                book.description = description
            if not book.isbn and isbn:
                book.isbn = isbn
            if not book.access_url and access_url:
                book.access_url = access_url

            # Add missing authors
            existing_author_names = {a.name.lower() for a in book.authors}
            for a_obj in author_objs:
                if a_obj.name.lower() not in existing_author_names:
                    book.authors.append(a_obj)
                    existing_author_names.add(a_obj.name.lower())

            # Add missing formats
            if formats_data:
                existing_fmts = {f.format.lower(): f for f in book.formats}
                for fmt_item in formats_data:
                    fmt_type = fmt_item["format"].lower()
                    if fmt_type not in existing_fmts:
                        new_fmt = BookFormat(
                            book_id=book.id,
                            format=fmt_type,
                            file_url=fmt_item["file_url"],
                            file_size=fmt_item.get("file_size"),
                            telegram_file_id=fmt_item.get("telegram_file_id"),
                            is_direct_download=fmt_item.get("is_direct_download", True)
                        )
                        self.session.add(new_fmt)
                        book.formats.append(new_fmt)

            await self.session.flush()

        # Always re-fetch fully eager loaded book object
        loaded_book = await self.get_by_id(book.id)
        return loaded_book or book
