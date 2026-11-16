from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from app.database.session import db_manager


class DatabaseMiddleware(BaseMiddleware):
    """Injects an AsyncSession into the handler data dictionary."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with db_manager.session_maker() as session:
            try:
                data["session"] = session
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
