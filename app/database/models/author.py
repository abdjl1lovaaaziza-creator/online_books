from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class Author(Base):
    """Book author model."""
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    birth_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    death_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    books: Mapped[List["Book"]] = relationship("Book", secondary="book_authors", back_populates="authors")

    def __repr__(self) -> str:
        return f"<Author name={self.name}>"
