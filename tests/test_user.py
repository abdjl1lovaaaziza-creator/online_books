import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.user import UserRepository
from app.config import settings


@pytest.mark.asyncio
async def test_user_registration_and_update(db_session: AsyncSession):
    """Test creating and retrieving users in the database."""
    repo = UserRepository(db_session)
    user, created = await repo.get_or_create(
        telegram_id=987654321,
        first_name="Jane",
        last_name="Doe",
        username="janedoe",
        language_code="en"
    )
    assert created is True
    assert user.telegram_id == 987654321
    assert user.first_name == "Jane"
    assert user.is_active is True

    # Retrieving same user should not create duplicate
    user2, created2 = await repo.get_or_create(
        telegram_id=987654321,
        first_name="Jane Updated",
        username="janedoe"
    )
    assert created2 is False
    assert user2.id == user.id
    assert user2.first_name == "Jane Updated"


@pytest.mark.asyncio
async def test_user_language_change(db_session: AsyncSession):
    """Test updating user preferred language."""
    repo = UserRepository(db_session)
    await repo.get_or_create(
        telegram_id=123123123,
        first_name="Alex",
        language_code="en"
    )

    success = await repo.update_language(123123123, "uz")
    assert success is True

    updated_user = await repo.get_by_telegram_id(123123123)
    assert updated_user.language_code == "uz"


@pytest.mark.asyncio
async def test_admin_check():
    """Verify administrator identification matches configured ADMIN_IDS."""
    # ADMIN_IDS in conftest set to "111222333,444555666"
    assert settings.is_admin(111222333) is True
    assert settings.is_admin(444555666) is True
    assert settings.is_admin(999999999) is False
