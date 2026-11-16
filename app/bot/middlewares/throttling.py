from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.config import settings
from app.services.cache import cache


class ThrottlingMiddleware(BaseMiddleware):
    """Rate limits excessive spamming or automated rapid requests."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        allowed = await cache.check_rate_limit(
            user_id=user.id,
            max_calls=settings.RATE_LIMIT_CALLS,
            period=settings.RATE_LIMIT_PERIOD
        )

        if not allowed:
            t = data.get("t")
            msg = t("errors.throttled") if t else "⏳ Please wait a moment before sending another request."
            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
            return None

        return await handler(event, data)
