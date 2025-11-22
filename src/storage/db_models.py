"""SQLAlchemy database models.

Maps domain models to PostgreSQL tables.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
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
from src.models.offer import OfferStatus
from src.models.purchase import PaymentProvider, PurchaseStatus


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class BusinessTable(Base):
    """Business entity table."""

    __tablename__ = "businesses"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, index=True)
    telegram_id = Column(Integer, nullable=False, unique=True, index=True)
    verification_status = Column(
        Enum(VerificationStatus, native_enum=True),
        nullable=False,
        default=VerificationStatus.PENDING,
        index=True,
    )
    photo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    venue = relationship("VenueTable", back_populates="business", uselist=False, cascade="all, delete-orphan")
    offers = relationship("OfferTable", back_populates="business", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_businesses_verification_status", verification_status),
        Index("ix_businesses_telegram_id", telegram_id),
    )


class VenueTable(Base):
    """Venue entity table."""

    __tablename__ = "venues"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id = Column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    address = Column(String(500), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)

    # Relationships
    business = relationship("BusinessTable", back_populates="venue")

    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="check_latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="check_longitude_range"),
        Index("ix_venues_coordinates", "latitude", "longitude"),
    )


class OfferTable(Base):
    """Offer entity table."""

    __tablename__ = "offers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id = Column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    items = Column(JSON, nullable=False)  # List of {name, unit_price, quantity_available}
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    status = Column(
        Enum(OfferStatus, native_enum=True),
        nullable=False,
        default=OfferStatus.DRAFT,
        index=True,
    )
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business = relationship("BusinessTable", back_populates="offers")
    purchases = relationship("PurchaseTable", back_populates="offer", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("start_time < end_time", name="check_time_range"),
        Index("ix_offers_status_end_time", status, end_time),
        Index("ix_offers_business_status", business_id, status),
    )


class CustomerTable(Base):
    """Customer entity table."""

    __tablename__ = "customers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    telegram_id = Column(Integer, nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PurchaseTable(Base):
    """Purchase entity table."""

    __tablename__ = "purchases"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    offer_id = Column(PG_UUID(as_uuid=True), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, nullable=False, index=True)  # Telegram user ID
    item_selections = Column(JSON, nullable=False)  # List of {item_name, quantity, unit_price}
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(
        Enum(PurchaseStatus, native_enum=True),
        nullable=False,
        default=PurchaseStatus.PENDING,
        index=True,
    )
    payment_provider = Column(
        Enum(PaymentProvider, native_enum=True),
        nullable=True,
    )
    payment_session_id = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    offer = relationship("OfferTable", back_populates="purchases")

    __table_args__ = (
        CheckConstraint("total_amount > 0", name="check_positive_total"),
        Index("ix_purchases_offer_status", offer_id, status),
        Index("ix_purchases_customer_id", customer_id),
    )
