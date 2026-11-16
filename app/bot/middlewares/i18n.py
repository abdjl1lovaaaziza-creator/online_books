from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.repositories.user import UserRepository
from app.localization.manager import i18n


class I18nMiddleware(BaseMiddleware):
    """
    Middleware ensuring user registration, active status check,
    and injecting translation helper 't' and 'user_lang' into handler data.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        tg_user: TgUser = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        session: AsyncSession = data.get("session")
        user_lang = settings.DEFAULT_LANGUAGE

        if session:
            try:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_telegram_id(tg_user.id)
                if user:
                    if not user.is_active:
                        # Drop updates for blocked users
                        logger.warning(f"Blocked user {tg_user.id} attempted interaction.")
                        return None
                    user_lang = user.language_code
                    data["user"] = user
                else:
                    # New user detected, register with preferred default
                    init_lang = tg_user.language_code[:2].lower() if tg_user.language_code else settings.DEFAULT_LANGUAGE
                    if init_lang not in settings.SUPPORTED_LANGUAGES:
                        init_lang = settings.DEFAULT_LANGUAGE
                    user_lang = init_lang
                    is_adm = settings.is_admin(tg_user.id)
                    user, _ = await user_repo.get_or_create(
                        telegram_id=tg_user.id,
                        first_name=tg_user.first_name,
                        last_name=tg_user.last_name,
                        username=tg_user.username,
                        language_code=user_lang,
                        is_admin=is_adm
                    )
                    data["user"] = user
            except Exception as e:
                logger.error(f"Error in I18nMiddleware DB lookup: {e}")

        data["user_lang"] = user_lang
        # Translation helper closure
        data["t"] = lambda key, **kwargs: i18n.get(key, lang=user_lang, **kwargs)

        return await handler(event, data)
