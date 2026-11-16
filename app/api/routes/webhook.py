from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request, status
from aiogram.types import Update
from loguru import logger

from app.config import settings
from app.bot.loader import bot, dp

router = APIRouter(tags=["Webhook"])


@router.post(settings.WEBHOOK_PATH)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None, alias="X-Telegram-Bot-Api-Secret-Token")
):
    """
    Telegram webhook callback endpoint.
    Strictly validates the secret token header provided by Telegram Bot API.
    """
    if x_telegram_bot_api_secret_token != settings.WEBHOOK_SECRET:
        logger.warning("Unauthorized webhook request with invalid or missing secret token.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token"
        )

    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_webhook_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        # Telegram expects HTTP 200 to acknowledge receipt and avoid retrying
        return {"ok": False, "error": str(e)}
