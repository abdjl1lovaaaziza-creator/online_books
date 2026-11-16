from typing import List, Optional
import httpx
from loguru import logger
from app.services.providers.base import BaseBookProvider, StandardBook, StandardBookFormat
from app.services.providers.open_library import nullcontext


class GutenbergProvider(BaseBookProvider):
    """Project Gutenberg provider via Gutendex JSON API."""

    name: str = "gutenberg"
    SEARCH_ENDPOINT: str = "https://gutendex.com/books"

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[StandardBook]:
        """Search public domain books in Project Gutenberg."""
        params = {"search": query}
        if language:
            params["languages"] = language[:2].lower()

        page = (offset // limit) + 1 if limit else 1
        if page > 1:
            params["page"] = page

        books: List[StandardBook] = []
        try:
            client = self._client or httpx.AsyncClient(timeout=10.0, follow_redirects=True)
            async with (client if not self._client else nullcontext()):
                response = await client.get(self.SEARCH_ENDPOINT, params=params)
                if response.status_code != 200:
                    logger.warning(f"Gutendex returned status {response.status_code}")
                    return []

                data = response.json()
                results = data.get("results", [])

                for item in results[:limit]:
                    title = item.get("title")
                    if not title:
                        continue

                    # Authors
                    authors_list = []
                    for author_dict in item.get("authors", []):
                        raw_name = author_dict.get("name", "")
                        if "," in raw_name:
                            parts = [p.strip() for p in raw_name.split(",")]
                            name = f"{parts[1]} {parts[0]}" if len(parts) > 1 else raw_name
                        else:
                            name = raw_name
                        authors_list.append(name)

                    # Languages
                    langs = item.get("languages", [])
                    lang = langs[0] if langs else (language or "en")

                    # Formats and Cover
                    formats_map = item.get("formats", {})
                    cover_url = formats_map.get("image/jpeg")

                    formats: List[StandardBookFormat] = []
                    # Check for EPUB
                    epub_url = formats_map.get("application/epub+zip")
                    if epub_url:
                        formats.append(
                            StandardBookFormat(format="epub", file_url=epub_url, is_direct_download=True)
                        )

                    # Check for TXT
                    txt_url = (
                        formats_map.get("text/plain; charset=utf-8")
                        or formats_map.get("text/plain; charset=us-ascii")
                        or formats_map.get("text/plain")
                    )
                    if txt_url:
                        formats.append(
                            StandardBookFormat(format="txt", file_url=txt_url, is_direct_download=True)
                        )

                    # Check for PDF or Octet-stream
                    pdf_url = formats_map.get("application/pdf")
                    if pdf_url:
                        formats.append(
                            StandardBookFormat(format="pdf", file_url=pdf_url, is_direct_download=True)
                        )

                    access_url = (
                        formats_map.get("text/html")
                        or formats_map.get("text/html; charset=utf-8")
                        or f"https://www.gutenberg.org/ebooks/{item.get('id')}"
                    )

                    subjects = item.get("subjects", [])
                    description = "; ".join(subjects[:3]) if subjects else "Project Gutenberg Public Domain Work"

                    books.append(
                        StandardBook(
                            title=title,
                            authors=authors_list[:3],
                            description=description,
                            language=lang,
                            publication_year=None,
                            publisher="Project Gutenberg",
                            isbn=None,
                            cover_url=cover_url,
                            source_name=self.name,
                            source_id=str(item.get("id")),
                            access_url=access_url,
                            license="Project Gutenberg Public Domain License",
                            is_textbook=False,
                            formats=formats
                        )
                    )
        except Exception as e:
            logger.error(f"Gutenberg search exception: {e}")

        return books
