from aiogram.filters import Filter
from aiogram.types import TelegramObject
from app.config import settings


class IsAdminFilter(Filter):
    """Filter ensuring user is authorized administrator via environment config."""

    async def __call__(self, event: TelegramObject, **kwargs) -> bool:
        user = getattr(event, "from_user", None)
        if not user:
            return False
        return settings.is_admin(user.id)
