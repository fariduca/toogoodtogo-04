"""User domain model."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User role enumeration."""

    BUSINESS = "BUSINESS"
    CUSTOMER = "CUSTOMER"


class User(BaseModel):
    """User entity representing both business owners and customers."""

    id: int = Field(description="Auto-increment primary key")
    telegram_user_id: int = Field(description="Telegram user ID", gt=0)
    telegram_username: Optional[str] = Field(default=None, max_length=100)
    role: UserRole = Field(description="User role")
    language_code: str = Field(default="en", min_length=2, max_length=2)
    notification_enabled: bool = Field(default=True)
    last_location_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    last_location_lon: Optional[float] = Field(default=None, ge=-180, le=180)
    last_location_updated: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserInput(BaseModel):
    """Input model for user creation."""

    telegram_user_id: int = Field(gt=0)
    telegram_username: Optional[str] = None
    role: UserRole
    language_code: str = Field(default="en", min_length=2, max_length=2)
