from typing import List, Optional
from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User account model mapping Telegram users to preferences and activity."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    downloads: Mapped[List["Download"]] = relationship("Download", back_populates="user", cascade="all, delete-orphan")
    search_history: Mapped[List["SearchHistory"]] = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} username={self.username} lang={self.language_code}>"
