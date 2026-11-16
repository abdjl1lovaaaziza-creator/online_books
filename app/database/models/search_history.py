from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class SearchHistory(Base):
    """User search queries log."""
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    filter_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="search_history")

    def __repr__(self) -> str:
        return f"<SearchHistory user_id={self.user_id} query={self.query!r}>"
