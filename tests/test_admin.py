import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.user import UserRepository
from app.config import settings
from app.bot.filters.admin import IsAdminFilter


class DummyEvent:
    def __init__(self, user_id: int):
        self.from_user = type("TgUser", (), {"id": user_id})()


@pytest.mark.asyncio
async def test_admin_filter():
    """Verify IsAdminFilter correctly approves configured admin IDs and rejects others."""
    admin_filter = IsAdminFilter()

    # Admin configured in conftest
    admin_event = DummyEvent(111222333)
    assert await admin_filter(admin_event) is True

    # Regular user
    regular_event = DummyEvent(999999999)
    assert await admin_filter(regular_event) is False


@pytest.mark.asyncio
async def test_admin_user_block_and_unblock(db_session: AsyncSession):
    """Test administrative user blocking and unblocking in database."""
    user_repo = UserRepository(db_session)
    user, _ = await user_repo.get_or_create(
        telegram_id=777888999,
        first_name="Spammer"
    )
    assert user.is_active is True

    # Block user
    await user_repo.set_active_status(777888999, is_active=False)
    await db_session.commit()

    blocked_user = await user_repo.get_by_telegram_id(777888999)
    assert blocked_user.is_active is False

    # Unblock user
    await user_repo.set_active_status(777888999, is_active=True)
    await db_session.commit()

    unblocked_user = await user_repo.get_by_telegram_id(777888999)
    assert unblocked_user.is_active is True
