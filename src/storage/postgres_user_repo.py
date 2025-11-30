"""PostgreSQL repository for User entities."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger
from src.models.user import User, UserInput, UserRole
from src.storage.db_models import UserTable
from src.storage.repository_base import RepositoryBase

logger = get_logger(__name__)


class PostgresUserRepository(RepositoryBase[User]):
    """User repository using PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_by_id(self, id: int) -> Optional[User]:
        """Retrieve user by ID."""
        stmt = select(UserTable).where(UserTable.id == id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            return None

        return self._to_domain_model(db_user)

    async def create(self, entity: UserInput) -> User:
        """Create new user."""
        db_user = UserTable(
            telegram_user_id=entity.telegram_user_id,
            telegram_username=entity.telegram_username,
            role=entity.role,
            language_code=entity.language_code,
        )

        self.session.add(db_user)
        await self.session.flush()

        logger.info(
            "user_created",
            user_id=db_user.id,
            telegram_user_id=entity.telegram_user_id,
            role=entity.role.value,
        )

        return self._to_domain_model(db_user)

    async def update(self, entity: User) -> User:
        """Update existing user."""
        stmt = select(UserTable).where(UserTable.id == entity.id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise ValueError(f"User not found: {entity.id}")

        db_user.telegram_username = entity.telegram_username
        db_user.language_code = entity.language_code
        db_user.notification_enabled = entity.notification_enabled
        db_user.last_location_lat = entity.last_location_lat
        db_user.last_location_lon = entity.last_location_lon
        db_user.last_location_updated = entity.last_location_updated

        await self.session.flush()

        logger.info("user_updated", user_id=entity.id)

        return self._to_domain_model(db_user)

    async def delete(self, id: int) -> bool:
        """Delete user by ID."""
        stmt = select(UserTable).where(UserTable.id == id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            return False

        await self.session.delete(db_user)
        await self.session.flush()

        logger.info("user_deleted", user_id=id)

        return True

    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID."""
        stmt = select(UserTable).where(UserTable.telegram_user_id == telegram_user_id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            return None

        return self._to_domain_model(db_user)

    async def get_by_role(self, role: UserRole) -> list[User]:
        """Get users by role."""
        stmt = select(UserTable).where(UserTable.role == role).order_by(UserTable.created_at.desc())
        result = await self.session.execute(stmt)
        db_users = result.scalars().all()

        return [self._to_domain_model(db_user) for db_user in db_users]

    async def update_location(
        self, user_id: int, latitude: float, longitude: float
    ) -> User:
        """Update user's last known location."""
        from datetime import datetime

        stmt = select(UserTable).where(UserTable.id == user_id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise ValueError(f"User not found: {user_id}")

        db_user.last_location_lat = latitude
        db_user.last_location_lon = longitude
        db_user.last_location_updated = datetime.utcnow()

        await self.session.flush()

        logger.info("user_location_updated", user_id=user_id)

        return self._to_domain_model(db_user)

    def _to_domain_model(self, db_user: UserTable) -> User:
        """Convert database model to domain model."""
        return User(
            id=db_user.id,
            telegram_user_id=db_user.telegram_user_id,
            telegram_username=db_user.telegram_username,
            role=db_user.role,
            language_code=db_user.language_code,
            notification_enabled=db_user.notification_enabled,
            last_location_lat=float(db_user.last_location_lat)
            if db_user.last_location_lat
            else None,
            last_location_lon=float(db_user.last_location_lon)
            if db_user.last_location_lon
            else None,
            last_location_updated=db_user.last_location_updated,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )
