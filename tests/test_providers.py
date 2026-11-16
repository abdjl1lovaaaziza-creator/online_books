import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.providers.open_library import OpenLibraryProvider
from app.services.providers.gutenberg import GutenbergProvider
from app.services.providers.google_books import GoogleBooksProvider
from app.services.providers.internet_archive import InternetArchiveProvider


@pytest.mark.asyncio
async def test_open_library_provider_parsing():
    """Verify Open Library API response parsing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "docs": [
            {
                "key": "/works/OL123W",
                "title": "Clean Code",
                "author_name": ["Robert C. Martin"],
                "first_publish_year": 2008,
                "publisher": ["Prentice Hall"],
                "isbn": ["9780132350884"],
                "cover_i": 12345,
                "language": ["eng"],
                "has_fulltext": True,
                "ia": ["cleancode0000mart"]
            }
        ]
    }
    mock_client.get = AsyncMock(return_value=mock_response)

    provider = OpenLibraryProvider(client=mock_client)
    books = await provider.search("Clean Code", limit=5)

    assert len(books) == 1
    book = books[0]
    assert book.title == "Clean Code"
    assert "Robert C. Martin" in book.authors
    assert book.publication_year == 2008
    assert book.isbn == "9780132350884"
    assert len(book.formats) == 2
    assert any(f.format == "pdf" for f in book.formats)


@pytest.mark.asyncio
async def test_gutenberg_provider_parsing():
    """Verify Project Gutenberg (Gutendex) parsing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": 1342,
                "title": "Pride and Prejudice",
                "authors": [{"name": "Austen, Jane", "birth_year": 1775, "death_year": 1817}],
                "subjects": ["Courtship -- Fiction", "Sisters -- Fiction"],
                "languages": ["en"],
                "formats": {
                    "application/epub+zip": "https://www.gutenberg.org/ebooks/1342.epub3.images",
                    "text/plain; charset=utf-8": "https://www.gutenberg.org/files/1342/1342-0.txt",
                    "image/jpeg": "https://www.gutenberg.org/cache/epub/1342/pg1342.cover.medium.jpg",
                    "text/html": "https://www.gutenberg.org/ebooks/1342.html.images"
                }
            }
        ]
    }
    mock_client.get = AsyncMock(return_value=mock_response)

    provider = GutenbergProvider(client=mock_client)
    books = await provider.search("Pride and Prejudice", limit=5)

    assert len(books) == 1
    book = books[0]
    assert book.title == "Pride and Prejudice"
    assert "Jane Austen" in book.authors
    assert book.cover_url is not None
    assert any(f.format == "epub" for f in book.formats)
    assert any(f.format == "txt" for f in book.formats)


@pytest.mark.asyncio
async def test_google_books_provider_parsing():
    """Verify Google Books API parsing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "abc123xyz",
                "volumeInfo": {
                    "title": "Introduction to Algorithms",
                    "authors": ["Thomas H. Cormen", "Charles E. Leiserson"],
                    "publishedDate": "2009-07-31",
                    "description": "Comprehensive textbook on algorithms.",
                    "categories": ["Computers / Educational / Textbooks"],
                    "industryIdentifiers": [
                        {"type": "ISBN_13", "identifier": "9780262033848"}
                    ]
                },
                "accessInfo": {
                    "viewability": "PARTIAL",
                    "publicDomain": False,
                    "webReaderLink": "https://play.google.com/books/reader?id=abc123xyz"
                }
            }
        ]
    }
    mock_client.get = AsyncMock(return_value=mock_response)

    provider = GoogleBooksProvider(client=mock_client)
    books = await provider.search("Algorithms", limit=5)

    assert len(books) == 1
    book = books[0]
    assert book.title == "Introduction to Algorithms"
    assert book.publication_year == 2009
    assert book.isbn == "9780262033848"
    assert book.is_textbook is True


@pytest.mark.asyncio
async def test_internet_archive_provider_parsing():
    """Verify Internet Archive texts parsing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": {
            "docs": [
                {
                    "identifier": "principlesofmath00russuoft",
                    "title": "The Principles of Mathematics",
                    "creator": ["Bertrand Russell"],
                    "year": "1903",
                    "description": "Classic foundational text in mathematical logic.",
                    "language": ["eng"],
                    "licenseurl": "http://creativecommons.org/publicdomain/mark/1.0/"
                }
            ]
        }
    }
    mock_client.get = AsyncMock(return_value=mock_response)

    provider = InternetArchiveProvider(client=mock_client)
    books = await provider.search("Russell Mathematics", limit=5)

    assert len(books) == 1
    book = books[0]
    assert book.title == "The Principles of Mathematics"
    assert book.publication_year == 1903
    assert any(f.format == "pdf" for f in book.formats)
