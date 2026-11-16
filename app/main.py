from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from app.config import settings
from app.database.session import db_manager
from app.services.cache import cache
from app.utils.seed import seed_categories
from app.bot import bot, dp, setup_bot
from app.api.routes.health import router as health_router
from app.api.routes.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing startup and graceful shutdown."""
    logger.info("Initializing Smart Library Telegram Bot...")

    # 1. Initialize Database Tables
    try:
        await db_manager.init_db()
        async with db_manager.session_maker() as session:
            await seed_categories(session)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # 2. Connect Cache
    await cache.connect()

    # 3. Setup Bot Handlers & Middlewares
    setup_bot()

    # 4. Register Telegram Webhook
    if settings.BOT_TOKEN and "REPLACE_WITH_REAL" not in settings.BOT_TOKEN:
        try:
            logger.info(f"Setting webhook to: {settings.full_webhook_url}")
            await bot.set_webhook(
                url=settings.full_webhook_url,
                secret_token=settings.WEBHOOK_SECRET,
                drop_pending_updates=True,
                allowed_updates=dp.resolve_used_update_types()
            )
            webhook_info = await bot.get_webhook_info()
            logger.info(f"Telegram Webhook configured: {webhook_info.url}")
        except Exception as e:
            logger.warning(f"Could not register Telegram webhook on startup: {e}")
    else:
        logger.warning("BOT_TOKEN is set to dummy/test value. Skipping Telegram set_webhook.")

    yield

    # Graceful Shutdown
    logger.info("Shutting down Smart Library Telegram Bot...")
    try:
        if settings.BOT_TOKEN and "REPLACE_WITH_REAL" not in settings.BOT_TOKEN:
            await bot.delete_webhook()
        await bot.session.close()
    except Exception as e:
        logger.warning(f"Error during bot session closure: {e}")

    await cache.close()
    await db_manager.close()
    logger.info("Smart Library Telegram Bot shutdown complete.")


app = FastAPI(
    title="Smart Library Telegram Bot API",
    description="High-performance asynchronous webhook API for Smart Library bot.",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routers
app.include_router(health_router)
app.include_router(webhook_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
