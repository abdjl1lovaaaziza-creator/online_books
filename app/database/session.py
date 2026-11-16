from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from loguru import logger
from app.config import settings
from app.database.models.base import Base


class DatabaseManager:
    """Manages Async SQLAlchemy engine and session generation."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        # SQLite async doesn't support pool_size or max_overflow
        is_sqlite = "sqlite" in self.database_url
        engine_kwargs = {
            "echo": settings.DEBUG,
            "future": True,
        }
        if not is_sqlite:
            engine_kwargs.update({
                "pool_size": 20,
                "max_overflow": 10,
                "pool_pre_ping": True,
                "pool_recycle": 1800,
            })

        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            **engine_kwargs
        )
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )

    async def init_db(self) -> None:
        """Create tables if they do not exist (useful for dev and testing)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")

    async def close(self) -> None:
        """Dispose of the database engine."""
        await self.engine.dispose()
        logger.info("Database engine closed.")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency for obtaining an async session."""
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


db_manager = DatabaseManager(settings.DATABASE_URL)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI & aiogram session dependency helper."""
    async for session in db_manager.get_session():
        yield session
