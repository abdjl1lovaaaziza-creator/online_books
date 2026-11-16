from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class Favorite(Base):
    """User book favorites list."""
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_book_favorite"),
    )

    user: Mapped["User"] = relationship("User", back_populates="favorites")
    book: Mapped["Book"] = relationship("Book", back_populates="favorites", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Favorite user_id={self.user_id} book_id={self.book_id}>"
