import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.book import BookRepository
from app.services.search import SearchService
from app.services.providers.base import BaseBookProvider, StandardBook, StandardBookFormat


class MockProvider(BaseBookProvider):
    name = "mock_provider"

    async def search(self, query: str, language=None, limit=10, offset=0):
        return [
            StandardBook(
                title=f"Discovered Book for {query}",
                authors=["Test Author"],
                description="A discovered book.",
                language="en",
                publication_year=2024,
                source_name=self.name,
                source_id=f"mock_{query}",
                license="Public Domain",
                formats=[
                    StandardBookFormat(format="pdf", file_url="https://example.com/test.pdf")
                ]
            )
        ]


@pytest.mark.asyncio
async def test_search_and_pagination(db_session: AsyncSession):
    """Test searching local database and pagination mechanics."""
    repo = BookRepository(db_session)

    # Insert test books
    for i in range(12):
        await repo.save_or_update(
            title=f"Python Programming Part {i + 1}",
            source_name="manual",
            source_id=f"manual_{i + 1}",
            description="Comprehensive guide to Python",
            language="en",
            publication_year=2020 + (i % 4),
            authors_names=["Guido van Rossum"],
            formats_data=[{"format": "pdf", "file_url": f"https://example.com/book_{i}.pdf"}]
        )
    await db_session.commit()

    # Page 1 (limit 5)
    books_p1, total = await repo.search(query="Python", limit=5, offset=0)
    assert total >= 12
    assert len(books_p1) == 5

    # Page 2 (offset 5)
    books_p2, total2 = await repo.search(query="Python", limit=5, offset=5)
    assert len(books_p2) == 5
    assert books_p1[0].id != books_p2[0].id

    # Search by author
    author_books, author_total = await repo.search(query="Guido", limit=5, offset=0)
    assert author_total >= 12


@pytest.mark.asyncio
async def test_unified_search_service_integration(db_session: AsyncSession):
    """Test search service queries providers and ingests results into DB."""
    service = SearchService(providers=[MockProvider()])

    books, total = await service.search(
        session=db_session,
        query="QuantumPhysics",
        limit=5,
        offset=0
    )

    assert total >= 1
    assert any("Discovered Book for QuantumPhysics" in b.title for b in books)
