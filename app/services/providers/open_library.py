from typing import List, Optional
import httpx
from loguru import logger
from app.services.providers.base import BaseBookProvider, StandardBook, StandardBookFormat


def normalize_language_code(code: Optional[str]) -> str:
    """Normalize language to standard 2-letter ISO-639-1 code."""
    if not code:
        return "ru"
    clean = code.lower().strip()
    mapping = {
        "rus": "ru",
        "ru": "ru",
        "russian": "ru",
        "eng": "en",
        "en": "en",
        "english": "en",
        "uzb": "uz",
        "uz": "uz",
        "tur": "tr",
        "tr": "tr",
        "ara": "ar",
        "ar": "ar",
        "deu": "de",
        "ger": "de",
        "de": "de",
        "fra": "fr",
        "fre": "fr",
        "fr": "fr",
        "spa": "es",
        "es": "es",
    }
    return mapping.get(clean, clean[:2] if len(clean) >= 2 else clean)


class OpenLibraryProvider(BaseBookProvider):
    """Open Library API provider (Internet Archive initiative)."""

    name: str = "open_library"
    BASE_URL: str = "https://openlibrary.org"
    SEARCH_ENDPOINT: str = f"{BASE_URL}/search.json"
    COVERS_BASE: str = "https://covers.openlibrary.org/b/id"

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[StandardBook]:
        """Search books via Open Library Search API with support for author and title modifiers."""
        page = (offset // limit) + 1 if limit else 1
        clean_q = query.strip()
        fields_str = "key,title,author_name,first_publish_year,publisher,isbn,cover_i,language,ia,public_scan_b,has_fulltext"

        if clean_q.startswith("inauthor:"):
            author_val = clean_q[len("inauthor:"):].strip()
            params = {
                "author": author_val,
                "limit": limit,
                "page": page,
                "fields": fields_str
            }
        elif clean_q.startswith("intitle:"):
            title_val = clean_q[len("intitle:"):].strip()
            params = {
                "title": title_val,
                "limit": limit,
                "page": page,
                "fields": fields_str
            }
        else:
            params = {
                "q": clean_q,
                "limit": limit,
                "page": page,
                "fields": fields_str
            }

        books: List[StandardBook] = []
        try:
            client = self._client or httpx.AsyncClient(timeout=10.0, follow_redirects=True)
            async with (client if not self._client else nullcontext()):
                response = await client.get(self.SEARCH_ENDPOINT, params=params)
                if response.status_code != 200:
                    logger.warning(f"OpenLibrary returned status {response.status_code}")
                    return []

                data = response.json()
                docs = data.get("docs", [])
                for doc in docs:
                    title = doc.get("title")
                    if not title:
                        continue

                    key = doc.get("key", "")
                    authors = doc.get("author_name", [])
                    year = doc.get("first_publish_year")
                    publishers = doc.get("publisher", [])
                    publisher = publishers[0] if publishers else None
                    isbns = doc.get("isbn", [])
                    isbn = isbns[0] if isbns else None

                    cover_id = doc.get("cover_i")
                    cover_url = f"{self.COVERS_BASE}/{cover_id}-L.jpg" if cover_id else None

                    langs = doc.get("language", [])
                    raw_lang = langs[0] if langs else (language or "ru")
                    lang = normalize_language_code(raw_lang)

                    access_url = f"{self.BASE_URL}{key}" if key else None

                    formats: List[StandardBookFormat] = []
                    ia_ids = doc.get("ia", [])
                    if ia_ids and (doc.get("has_fulltext") or doc.get("public_scan_b")):
                        ia_id = ia_ids[0]
                        formats.append(
                            StandardBookFormat(
                                format="pdf",
                                file_url=f"https://archive.org/download/{ia_id}/{ia_id}.pdf",
                                is_direct_download=True
                            )
                        )
                        formats.append(
                            StandardBookFormat(
                                format="epub",
                                file_url=f"https://archive.org/download/{ia_id}/{ia_id}_epub.epub",
                                is_direct_download=True
                            )
                        )

                    books.append(
                        StandardBook(
                            title=title,
                            authors=authors[:3],
                            description=None,
                            language=lang,
                            publication_year=int(year) if year else None,
                            publisher=publisher,
                            isbn=isbn,
                            cover_url=cover_url,
                            source_name=self.name,
                            source_id=key,
                            access_url=access_url,
                            license="Public Domain / Open Access",
                            is_textbook=False,
                            formats=formats
                        )
                    )
        except Exception as e:
            logger.error(f"OpenLibrary search exception: {e}")

        return books


class nullcontext:
    """Async context manager helper when external client is reused."""
    async def __aenter__(self):
        return None
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
