from typing import List, Optional
import httpx
from loguru import logger
from app.services.providers.base import BaseBookProvider, StandardBook, StandardBookFormat
from app.services.providers.open_library import nullcontext


class InternetArchiveProvider(BaseBookProvider):
    """Internet Archive texts API provider."""

    name: str = "internet_archive"
    SEARCH_ENDPOINT: str = "https://archive.org/advancedsearch.php"
    DOWNLOAD_BASE: str = "https://archive.org/download"
    IMG_BASE: str = "https://archive.org/services/img"

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[StandardBook]:
        """Search texts and open books in Internet Archive."""
        q_str = f'({query}) AND mediatype:(texts)'
        if language:
            q_str += f' AND language:({language[:3].lower()})'

        page = (offset // limit) + 1 if limit else 1
        params = {
            "q": q_str,
            "fl[]": ["identifier", "title", "creator", "year", "description", "licenseurl", "language"],
            "sort[]": "downloads desc",
            "rows": limit,
            "page": page,
            "output": "json"
        }

        books: List[StandardBook] = []
        try:
            client = self._client or httpx.AsyncClient(timeout=10.0, follow_redirects=True)
            async with (client if not self._client else nullcontext()):
                response = await client.get(self.SEARCH_ENDPOINT, params=params)
                if response.status_code != 200:
                    logger.warning(f"Internet Archive returned status {response.status_code}")
                    return []

                data = response.json()
                docs = data.get("response", {}).get("docs", [])

                for doc in docs:
                    identifier = doc.get("identifier")
                    title = doc.get("title")
                    if not identifier or not title:
                        continue

                    creators = doc.get("creator", [])
                    if isinstance(creators, str):
                        creators = [creators]

                    year_raw = doc.get("year")
                    year = int(year_raw) if str(year_raw).isdigit() else None

                    desc = doc.get("description")
                    if isinstance(desc, list):
                        desc = " ".join(desc)

                    lang_raw = doc.get("language", language or "en")
                    lang = lang_raw[0] if isinstance(lang_raw, list) and lang_raw else str(lang_raw)

                    cover_url = f"{self.IMG_BASE}/{identifier}"
                    access_url = f"https://archive.org/details/{identifier}"
                    license_url = doc.get("licenseurl") or "Open Access (Internet Archive)"

                    formats = [
                        StandardBookFormat(
                            format="pdf",
                            file_url=f"{self.DOWNLOAD_BASE}/{identifier}/{identifier}.pdf",
                            is_direct_download=True
                        ),
                        StandardBookFormat(
                            format="epub",
                            file_url=f"{self.DOWNLOAD_BASE}/{identifier}/{identifier}_epub.epub",
                            is_direct_download=True
                        ),
                        StandardBookFormat(
                            format="txt",
                            file_url=f"{self.DOWNLOAD_BASE}/{identifier}/{identifier}_djvu.txt",
                            is_direct_download=True
                        ),
                    ]

                    books.append(
                        StandardBook(
                            title=title,
                            authors=creators[:3],
                            description=desc[:500] if desc else None,
                            language=lang,
                            publication_year=year,
                            publisher="Internet Archive",
                            isbn=None,
                            cover_url=cover_url,
                            source_name=self.name,
                            source_id=identifier,
                            access_url=access_url,
                            license=license_url,
                            is_textbook=False,
                            formats=formats
                        )
                    )
        except Exception as e:
            logger.error(f"Internet Archive search exception: {e}")

        return books
