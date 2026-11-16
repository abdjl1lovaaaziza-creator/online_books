from typing import List, Optional
import httpx
from loguru import logger
from app.config import settings
from app.services.providers.base import BaseBookProvider, StandardBook, StandardBookFormat
from app.services.providers.open_library import nullcontext


class GoogleBooksProvider(BaseBookProvider):
    """Google Books API provider with open access / public domain detection."""

    name: str = "google_books"
    SEARCH_ENDPOINT: str = "https://www.googleapis.com/books/v1/volumes"

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[StandardBook]:
        """Search books via Google Books API."""
        params = {
            "q": query,
            "maxResults": min(limit, 20),
            "startIndex": offset,
        }
        if language:
            params["langRestrict"] = language[:2].lower()
        if settings.GOOGLE_BOOKS_API_KEY:
            params["key"] = settings.GOOGLE_BOOKS_API_KEY

        books: List[StandardBook] = []
        try:
            client = self._client or httpx.AsyncClient(timeout=10.0, follow_redirects=True)
            async with (client if not self._client else nullcontext()):
                response = await client.get(self.SEARCH_ENDPOINT, params=params)
                if response.status_code != 200:
                    logger.warning(f"Google Books API returned status {response.status_code}")
                    return []

                data = response.json()
                items = data.get("items", [])
                for item in items:
                    v_info = item.get("volumeInfo", {})
                    a_info = item.get("accessInfo", {})

                    title = v_info.get("title")
                    if not title:
                        continue

                    authors = v_info.get("authors", [])
                    pub_date = v_info.get("publishedDate", "")
                    year = None
                    if pub_date and len(pub_date) >= 4 and pub_date[:4].isdigit():
                        year = int(pub_date[:4])

                    publisher = v_info.get("publisher")
                    description = v_info.get("description")
                    lang = v_info.get("language", language or "en")

                    # Extract ISBN
                    isbn = None
                    for id_item in v_info.get("industryIdentifiers", []):
                        if id_item.get("type") in ("ISBN_13", "ISBN_10"):
                            isbn = id_item.get("identifier")
                            break

                    # Cover
                    img_links = v_info.get("imageLinks", {})
                    cover_url = img_links.get("thumbnail") or img_links.get("smallThumbnail")
                    if cover_url and cover_url.startswith("http://"):
                        cover_url = "https://" + cover_url[7:]

                    access_url = a_info.get("webReaderLink") or v_info.get("previewLink") or v_info.get("infoLink")

                    # Extract open formats
                    formats: List[StandardBookFormat] = []
                    pdf_info = a_info.get("pdf", {})
                    if pdf_info.get("isAvailable"):
                        dl_link = pdf_info.get("downloadLink") or pdf_info.get("acsTokenLink")
                        if dl_link:
                            formats.append(
                                StandardBookFormat(
                                    format="pdf",
                                    file_url=dl_link,
                                    is_direct_download=bool(pdf_info.get("downloadLink"))
                                )
                            )

                    epub_info = a_info.get("epub", {})
                    if epub_info.get("isAvailable"):
                        dl_link = epub_info.get("downloadLink") or epub_info.get("acsTokenLink")
                        if dl_link:
                            formats.append(
                                StandardBookFormat(
                                    format="epub",
                                    file_url=dl_link,
                                    is_direct_download=bool(epub_info.get("downloadLink"))
                                )
                            )

                    viewability = a_info.get("viewability", "")
                    is_public_domain = a_info.get("publicDomain", False)
                    license_str = "Public Domain" if is_public_domain else (viewability or "Google Books Open Preview")

                    # Textbook heuristic
                    categories = v_info.get("categories", [])
                    is_textbook = any(
                        "textbook" in c.lower() or "study aid" in c.lower() or "education" in c.lower()
                        for c in categories
                    )

                    books.append(
                        StandardBook(
                            title=title,
                            authors=authors[:3],
                            description=description[:500] if description else None,
                            language=lang,
                            publication_year=year,
                            publisher=publisher,
                            isbn=isbn,
                            cover_url=cover_url,
                            source_name=self.name,
                            source_id=item.get("id"),
                            access_url=access_url,
                            license=license_str,
                            is_textbook=is_textbook,
                            formats=formats
                        )
                    )
        except Exception as e:
            logger.error(f"Google Books search exception: {e}")

        return books
