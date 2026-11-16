from typing import List, Optional
import httpx
from loguru import logger
from app.services.providers.base import BaseBookProvider, StandardBook, StandardBookFormat


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
        """Search books via Open Library Search API."""
        page = (offset // limit) + 1 if limit else 1
        params = {
            "q": query,
            "limit": limit,
            "page": page,
            "fields": "key,title,author_name,first_publish_year,publisher,isbn,cover_i,language,ia,public_scan_b,has_fulltext"
        }
        if language:
            params["lang"] = language[:3].lower()

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
                    lang = langs[0] if langs else (language or "en")

                    access_url = f"{self.BASE_URL}{key}" if key else None

                    formats: List[StandardBookFormat] = []
                    ia_ids = doc.get("ia", [])
                    if ia_ids and (doc.get("has_fulltext") or doc.get("public_scan_b")):
                        ia_id = ia_ids[0]
                        # Internet Archive open access direct formats
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
