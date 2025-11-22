"""Database connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config.settings import Settings, load_settings
from src.logging import get_logger
from src.storage.db_models import Base

logger = get_logger(__name__)


class Database:
    """Database connection manager."""

    def __init__(self, settings: Settings):
        """
        Initialize database connection.

        Args:
            settings: Application settings with database URL
        """
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: sessionmaker | None = None

    async def connect(self) -> None:
        """Create database engine and session factory."""
        if self._engine is not None:
            return

        # Create async engine
        self._engine = create_async_engine(
            self.settings.database_url,
            echo=self.settings.log_level == "DEBUG",
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )

        # Create session factory
        self._session_factory = sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("database_connected", url=self._mask_password(self.settings.database_url))

    async def disconnect(self) -> None:
        """Close database connections."""
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None

        logger.info("database_disconnected")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Get database session context manager.

        Yields:
            AsyncSession for database operations

        Example:
            async with db.session() as session:
                result = await session.execute(query)
                await session.commit()
        """
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_tables(self) -> None:
        """Create all database tables. Use migrations in production."""
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("database_tables_created")

    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if "@" in url:
            # postgresql://user:password@host/db -> postgresql://user:***@host/db
            parts = url.split("@")
            if ":" in parts[0]:
                user_part = parts[0].rsplit(":", 1)[0]
                return f"{user_part}:***@{parts[1]}"
        return url


# Global database instance
_db_instance: Database | None = None


def get_database() -> Database:
    """Get or create global database instance."""
    global _db_instance
    if _db_instance is None:
        settings = load_settings()
        _db_instance = Database(settings)
    return _db_instance
