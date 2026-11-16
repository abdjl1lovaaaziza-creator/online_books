import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.config import settings


@pytest.mark.asyncio
async def test_health_check_endpoint(api_client: AsyncClient):
    """Verify /health endpoint returns 200 and accurate system information."""
    response = await api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "uptime_seconds" in data
    assert "database" in data
    assert "cache" in data


@pytest.mark.asyncio
async def test_webhook_missing_secret_token(api_client: AsyncClient):
    """Webhook must reject requests lacking X-Telegram-Bot-Api-Secret-Token."""
    response = await api_client.post(
        settings.WEBHOOK_PATH,
        json={"update_id": 10001}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid secret token"


@pytest.mark.asyncio
async def test_webhook_invalid_secret_token(api_client: AsyncClient):
    """Webhook must reject requests with wrong secret token."""
    response = await api_client.post(
        settings.WEBHOOK_PATH,
        json={"update_id": 10001},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret_token"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_valid_token_and_update(api_client: AsyncClient):
    """Webhook accepts request with valid token and dispatches to aiogram."""
    update_payload = {
        "update_id": 999999,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {
                "id": 123456,
                "is_bot": False,
                "first_name": "TestUser",
                "language_code": "en"
            },
            "text": "/start"
        }
    }

    with patch("app.bot.loader.dp.feed_webhook_update", new_callable=AsyncMock) as mock_feed:
        mock_feed.return_value = None
        response = await api_client.post(
            settings.WEBHOOK_PATH,
            json=update_payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": settings.WEBHOOK_SECRET}
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        assert mock_feed.called
