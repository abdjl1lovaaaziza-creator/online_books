from app.bot.loader import bot, dp
from app.bot.middlewares.database import DatabaseMiddleware
from app.bot.middlewares.i18n import I18nMiddleware
from app.bot.middlewares.throttling import ThrottlingMiddleware

from app.bot.handlers import (
    start,
    menu,
    search,
    book_details,
    categories,
    favorites,
    downloads,
    admin
)


def setup_bot():
    """Register all middlewares, routers, and filters."""
    # Middlewares registration (order matters)
    # 1. Throttling
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    # 2. Database session injection
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    # 3. I18n / user localization
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())

    # Router registration
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(categories.router)
    dp.include_router(favorites.router)
    dp.include_router(downloads.router)
    dp.include_router(book_details.router)
    dp.include_router(search.router)


__all__ = ["bot", "dp", "setup_bot"]
