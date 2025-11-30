"""Business and Venue domain models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class VerificationStatus(str, Enum):
    """Business verification status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Venue(BaseModel):
    """Venue location details."""

    street_address: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country_code: str = Field(default="FI", min_length=2, max_length=2)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class BusinessInput(BaseModel):
    """Input model for business registration."""

    business_name: str = Field(min_length=3, max_length=200)
    owner_id: int = Field(description="User ID of the business owner")
    street_address: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country_code: str = Field(default="FI", min_length=2, max_length=2)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    phone: Optional[str] = Field(default=None, max_length=20)
    logo_url: Optional[str] = None


class Business(BaseModel):
    """Business entity."""

    id: UUID = Field(default_factory=uuid4)
    owner_id: int = Field(description="User ID of the business owner")
    business_name: str = Field(min_length=3, max_length=200)
    venue: Venue
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    logo_url: Optional[str] = None
    verification_status: VerificationStatus = Field(default=VerificationStatus.PENDING)
    verification_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
