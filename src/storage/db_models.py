"""SQLAlchemy database models.

Maps domain models to PostgreSQL tables.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, relationship

from src.models.business import VerificationStatus
from src.models.offer import OfferCategory, OfferStatus
from src.models.reservation import ReservationStatus
from src.models.user import UserRole


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class UserTable(Base):
    """User entity table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id = Column(BigInteger, nullable=False, unique=True, index=True)
    telegram_username = Column(String(100), nullable=True)
    role = Column(
        Enum(UserRole, native_enum=True),
        nullable=False,
        index=True,
    )
    language_code = Column(String(2), nullable=False, default="en")
    notification_enabled = Column(Boolean, nullable=False, default=True)
    last_location_lat = Column(Numeric(9, 6), nullable=True)
    last_location_lon = Column(Numeric(9, 6), nullable=True)
    last_location_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    businesses = relationship("BusinessTable", back_populates="owner", foreign_keys="BusinessTable.owner_id")
    reservations = relationship("ReservationTable", back_populates="customer", foreign_keys="ReservationTable.customer_id")

    __table_args__ = (
        Index("ix_users_telegram_user_id", telegram_user_id),
        Index("ix_users_role", role),
    )


class BusinessTable(Base):
    """Business entity table."""

    __tablename__ = "businesses"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_name = Column(String(200), nullable=False, index=True)
    street_address = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country_code = Column(String(2), nullable=False, default="FI")
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    logo_url = Column(String(500), nullable=True)
    verification_status = Column(
        Enum(VerificationStatus, native_enum=True),
        nullable=False,
        default=VerificationStatus.PENDING,
        index=True,
    )
    verification_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("UserTable", back_populates="businesses", foreign_keys=[owner_id])
    offers = relationship("OfferTable", back_populates="business", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_businesses_owner_id", owner_id),
        Index("ix_businesses_verification_status", verification_status),
        Index("ix_businesses_location", latitude, longitude),
        Index("ix_businesses_name_postal", business_name, postal_code, unique=True),
    )


class OfferTable(Base):
    """Offer entity table."""

    __tablename__ = "offers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id = Column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    photo_url = Column(String(500), nullable=True)
    category = Column(Enum(OfferCategory, native_enum=True), nullable=True)
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    quantity_total = Column(Integer, nullable=False)
    quantity_remaining = Column(Integer, nullable=False)
    pickup_start_time = Column(DateTime, nullable=False)
    pickup_end_time = Column(DateTime, nullable=False, index=True)
    state = Column(
        Enum(OfferStatus, native_enum=True),
        nullable=False,
        default=OfferStatus.ACTIVE,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business = relationship("BusinessTable", back_populates="offers")
    reservations = relationship("ReservationTable", back_populates="offer", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("pickup_start_time < pickup_end_time", name="check_time_range"),
        CheckConstraint("price_per_unit > 0", name="check_positive_price"),
        CheckConstraint("quantity_total > 0", name="check_positive_total_quantity"),
        CheckConstraint("quantity_remaining >= 0", name="check_nonnegative_remaining"),
        CheckConstraint("quantity_remaining <= quantity_total", name="check_remaining_le_total"),
        Index("ix_offers_state_pickup_end", state, pickup_end_time),
        Index("ix_offers_state_created", state, created_at.desc()),
        Index("ix_offers_business_state", business_id, state),
        Index("ix_offers_category", category),
    )


class ReservationTable(Base):
    """Reservation entity table."""

    __tablename__ = "reservations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(String(12), nullable=False, unique=True, index=True)
    offer_id = Column(PG_UUID(as_uuid=True), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    status = Column(
        Enum(ReservationStatus, native_enum=True),
        nullable=False,
        default=ReservationStatus.CONFIRMED,
        index=True,
    )
    pickup_start_time = Column(DateTime, nullable=False)
    pickup_end_time = Column(DateTime, nullable=False)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    offer = relationship("OfferTable", back_populates="reservations")
    customer = relationship("UserTable", back_populates="reservations", foreign_keys=[customer_id])

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        CheckConstraint("unit_price > 0", name="check_positive_unit_price"),
        CheckConstraint("total_price > 0", name="check_positive_total_price"),
        Index("ix_reservations_offer_id", offer_id),
        Index("ix_reservations_customer_id", customer_id),
        Index("ix_reservations_order_id", order_id, unique=True),
        Index("ix_reservations_customer_created", customer_id, created_at.desc()),
        Index("ix_reservations_status", status),
    )
