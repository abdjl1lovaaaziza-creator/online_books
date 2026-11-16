from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class StandardBookFormat(BaseModel):
    """Normalized file format information across providers."""
    format: str = Field(description="Format extension: pdf, epub, fb2, djvu, txt, mobi, docx")
    file_url: str = Field(description="Direct download URL or reading page URL")
    file_size: Optional[int] = Field(default=None, description="Size in bytes, if provided by source")
    is_direct_download: bool = Field(default=True, description="True if link directly downloads the file")


class StandardBook(BaseModel):
    """Standardized book metadata representation."""
    title: str
    original_title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    language: str = "en"
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    cover_url: Optional[str] = None
    source_name: str
    source_id: Optional[str] = None
    access_url: Optional[str] = None
    license: str = "Public Domain / Open Access"
    is_textbook: bool = False
    formats: List[StandardBookFormat] = Field(default_factory=list)


class BaseBookProvider(ABC):
    """Abstract base class for all book repository providers."""

    name: str = "base"
    is_enabled: bool = True

    @abstractmethod
    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[StandardBook]:
        """Search books in provider repository."""
        pass
