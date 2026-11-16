from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, BigInteger, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class BookFormat(Base):
    """File formats available for downloading or reading a book."""
    __tablename__ = "book_formats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, epub, fb2, djvu, txt, mobi, docx
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # size in bytes
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    is_direct_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    book: Mapped["Book"] = relationship("Book", back_populates="formats")

    def __repr__(self) -> str:
        return f"<BookFormat format={self.format} book_id={self.book_id}>"
