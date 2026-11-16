from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import User as TgUser

from app.config import settings
from app.database.models.user import User
from app.database.repositories.user import UserRepository
from app.database.repositories.favorite import FavoriteRepository
from app.database.repositories.download import DownloadRepository


class UserService:
    """Manages user registration, profiles, and statistics."""

    async def register_or_update(
        self,
        session: AsyncSession,
        tg_user: TgUser
    ) -> Tuple[User, bool]:
        """Register a new user or update details."""
        repo = UserRepository(session)
        is_admin = settings.is_admin(tg_user.id)
        # Determine language code: if tg_user language in supported, use it, else default
        lang = tg_user.language_code[:2].lower() if tg_user.language_code else settings.DEFAULT_LANGUAGE
        if lang not in settings.SUPPORTED_LANGUAGES:
            lang = settings.DEFAULT_LANGUAGE

        user, created = await repo.get_or_create(
            telegram_id=tg_user.id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            username=tg_user.username,
            language_code=lang,
            is_admin=is_admin
        )
        return user, created

    async def change_language(self, session: AsyncSession, telegram_id: int, new_lang: str) -> bool:
        """Change preferred language."""
        if new_lang not in settings.SUPPORTED_LANGUAGES:
            return False
        repo = UserRepository(session)
        return await repo.update_language(telegram_id, new_lang)

    async def get_stats(self, session: AsyncSession, telegram_id: int) -> dict:
        """Get statistics for user profile."""
        user_repo = UserRepository(session)
        fav_repo = FavoriteRepository(session)
        dl_repo = DownloadRepository(session)

        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return {}

        fav_count = await fav_repo.count_user_favorites(user.id)
        dl_count = await dl_repo.count_user_downloads(user.id)

        return {
            "user_id": user.telegram_id,
            "language": user.language_code,
            "registered_date": user.created_at.strftime("%Y-%m-%d"),
            "favorites_count": fav_count,
            "downloads_count": dl_count,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
        }


user_service = UserService()
