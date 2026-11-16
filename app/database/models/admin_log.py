from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.models.base import Base


class AdminLog(Base):
    """Audit trail for administrator activities."""
    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<AdminLog admin={self.admin_telegram_id} action={self.action}>"
