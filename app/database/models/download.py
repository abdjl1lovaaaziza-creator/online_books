from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class Download(Base):
    """User download event tracking for statistics and history."""
    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="downloads")
    book: Mapped["Book"] = relationship("Book", back_populates="downloads", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Download user_id={self.user_id} book_id={self.book_id} format={self.format}>"
