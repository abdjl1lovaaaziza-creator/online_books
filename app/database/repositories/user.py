from typing import Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.user import User


class UserRepository:
    """Data access repository for users."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Fetch user by Telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: str = "en",
        is_admin: bool = False
    ) -> tuple[User, bool]:
        """Fetch existing user or register a new user."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Update dynamic fields if changed
            updated = False
            if user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if user.username != username:
                user.username = username
                updated = True
            if is_admin and not user.is_admin:
                user.is_admin = True
                updated = True
            if updated:
                await self.session.flush()
            return user, False

        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
            is_admin=is_admin,
            is_active=True
        )
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def update_language(self, telegram_id: int, language_code: str) -> bool:
        """Update user's preferred interface language."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(language_code=language_code)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def set_active_status(self, telegram_id: int, is_active: bool) -> bool:
        """Block or unblock user."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_active=is_active)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def count_total_users(self) -> int:
        """Get total registered user count."""
        stmt = select(func.count(User.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_active_users(self) -> int:
        """Get active user count."""
        stmt = select(func.count(User.id)).where(User.is_active == True)  # noqa: E712
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_all_active_telegram_ids(self) -> List[int]:
        """Fetch all active user Telegram IDs for broadcast announcements."""
        stmt = select(User.telegram_id).where(User.is_active == True)  # noqa: E712
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]
