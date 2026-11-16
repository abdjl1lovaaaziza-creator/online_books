from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.models.base import Base


class BookSource(Base):
    """External book source/provider registry."""
    __tablename__ = "book_sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_key: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<BookSource code={self.code} enabled={self.is_enabled}>"
