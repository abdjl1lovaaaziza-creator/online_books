import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

# Set test environment variables before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["BOT_TOKEN"] = "123456789:TESTING_BOT_TOKEN_NOT_REAL"
os.environ["WEBHOOK_SECRET"] = "test_webhook_secret_1234567890"
os.environ["ADMIN_IDS"] = "111222333,444555666"

from app.config import settings
from app.database.models.base import Base
from app.database.session import db_manager
from app.services.cache import cache
from app.utils.seed import seed_categories
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create in-memory SQLite async test engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Point db_manager to test engine
    db_manager.engine = engine
    db_manager.session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    # Seed categories
    async with db_manager.session_maker() as session:
        await seed_categories(session)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for each test."""
    async with db_manager.session_maker() as session:
        yield session
        # Clean up any uncommitted work
        await session.rollback()


@pytest_asyncio.fixture
async def api_client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints."""
    # Ensure cache in-memory fallback is active
    await cache.connect()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
