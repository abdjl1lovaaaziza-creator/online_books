import asyncio
from typing import List, Optional, Tuple
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.book import Book
from app.database.repositories.book import BookRepository
from app.services.cache import cache
from app.services.providers.base import BaseBookProvider, StandardBook
from app.services.providers.open_library import OpenLibraryProvider
from app.services.providers.gutenberg import GutenbergProvider
from app.services.providers.google_books import GoogleBooksProvider
from app.services.providers.internet_archive import InternetArchiveProvider


class SearchService:
    """Unified search service orchestrating database queries and external open book providers."""

    def __init__(self, providers: Optional[List[BaseBookProvider]] = None):
        self.providers = providers or [
            OpenLibraryProvider(),
            GutenbergProvider(),
            GoogleBooksProvider(),
            InternetArchiveProvider(),
        ]

    async def search(
        self,
        session: AsyncSession,
        query: str,
        language: Optional[str] = None,
        file_format: Optional[str] = None,
        year: Optional[int] = None,
        category_id: Optional[int] = None,
        is_textbook: Optional[bool] = None,
        limit: int = 5,
        offset: int = 0
    ) -> Tuple[List[Book], int]:
        """
        Unified search:
        1. Searches local database.
        2. If database has fewer results than required and query is provided, queries external providers.
        3. Saves discovered books into DB for indexing, caching, and relations.
        4. Returns paginated database Book objects and total count.
        """
        book_repo = BookRepository(session)

        # First, search local database
        local_books, local_total = await book_repo.search(
            query=query,
            language=language,
            file_format=file_format,
            year=year,
            category_id=category_id,
            is_textbook=is_textbook,
            limit=limit,
            offset=offset
        )

        # If we have enough results or it's a category/filter browse without text query, return local
        if (local_total >= (offset + limit)) or not query:
            return local_books, local_total

        # Query external providers concurrently
        provider_tasks = [
            provider.search(
                query=query,
                language=language,
                limit=limit,
                offset=0
            )
            for provider in self.providers
            if provider.is_enabled
        ]

        results = await asyncio.gather(*provider_tasks, return_exceptions=True)

        discovered_books: List[StandardBook] = []
        for res in results:
            if isinstance(res, list):
                discovered_books.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Provider search failed: {res}")

        # Ingest discovered books into local DB
        saved_book_ids: List[int] = []
        for std_book in discovered_books:
            try:
                formats_data = [
                    {
                        "format": f.format,
                        "file_url": f.file_url,
                        "file_size": f.file_size,
                        "is_direct_download": f.is_direct_download,
                    }
                    for f in std_book.formats
                ]
                saved_b = await book_repo.save_or_update(
                    title=std_book.title,
                    source_name=std_book.source_name,
                    source_id=std_book.source_id,
                    original_title=std_book.original_title,
                    description=std_book.description,
                    language=std_book.language,
                    publication_year=std_book.publication_year,
                    publisher=std_book.publisher,
                    isbn=std_book.isbn,
                    cover_url=std_book.cover_url,
                    access_url=std_book.access_url,
                    license_str=std_book.license,
                    is_textbook=std_book.is_textbook,
                    authors_names=std_book.authors,
                    formats_data=formats_data
                )
                if saved_b and saved_b.id:
                    saved_book_ids.append(saved_b.id)
            except Exception as e:
                logger.warning(f"Error persisting discovered book {std_book.title}: {e}")

        await session.commit()

        # Re-fetch from DB to get normalized, sorted results with IDs
        updated_books, total_count = await book_repo.search(
            query=query,
            language=language,
            file_format=file_format,
            year=year,
            category_id=category_id,
            is_textbook=is_textbook,
            limit=limit,
            offset=offset
        )

        # Fallback to books directly saved from this discovery session if transliteration/case differed
        if not updated_books and saved_book_ids:
            fallback_stmt = (
                select(Book)
                .options(
                    selectinload(Book.authors),
                    selectinload(Book.categories),
                    selectinload(Book.formats)
                )
                .where(Book.id.in_(saved_book_ids))
                .order_by(Book.id.desc())
                .offset(offset)
                .limit(limit)
            )
            fallback_res = await session.execute(fallback_stmt)
            fallback_books = list(fallback_res.scalars().all())
            if fallback_books:
                return fallback_books, len(saved_book_ids)

        return updated_books, total_count


search_service = SearchService()
