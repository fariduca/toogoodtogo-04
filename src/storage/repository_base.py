"""Repository base interface."""

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar
from uuid import UUID

T = TypeVar("T")


class RepositoryBase(ABC, Generic[T]):
    """Base repository interface for CRUD operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Retrieve entity by ID."""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        pass
