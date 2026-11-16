from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class Category(Base):
    """Subject and educational category model."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False)
    name_uz: Mapped[str] = mapped_column(String(100), nullable=False)
    name_tr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="📚", nullable=False)
    is_textbook: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    books: Mapped[List["Book"]] = relationship("Book", secondary="book_categories", back_populates="categories")

    def get_name(self, lang: str = "en") -> str:
        """Get localized category title."""
        field_name = f"name_{lang.lower()}"
        return getattr(self, field_name, self.name_en) or self.name_en

    def __repr__(self) -> str:
        return f"<Category slug={self.slug} name_en={self.name_en}>"
