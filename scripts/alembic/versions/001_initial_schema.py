"""Initial schema with businesses, venues, offers, purchases

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create enum types
    op.execute("CREATE TYPE verificationstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED')")
    op.execute("CREATE TYPE offerstatus AS ENUM ('DRAFT', 'ACTIVE', 'PAUSED', 'EXPIRED', 'SOLD_OUT')")
    op.execute("CREATE TYPE purchasestatus AS ENUM ('PENDING', 'CONFIRMED', 'CANCELED')")
    op.execute("CREATE TYPE paymentprovider AS ENUM ('STRIPE')")

    # Create businesses table
    op.create_table(
        'businesses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('verification_status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', name='verificationstatus', create_type=False), nullable=False),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_businesses_name', 'businesses', ['name'])
    op.create_index('ix_businesses_telegram_id', 'businesses', ['telegram_id'], unique=True)
    op.create_index('ix_businesses_verification_status', 'businesses', ['verification_status'])

    # Create venues table
    op.create_table(
        'venues',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=False),
        sa.CheckConstraint('latitude >= -90 AND latitude <= 90', name='check_latitude_range'),
        sa.CheckConstraint('longitude >= -180 AND longitude <= 180', name='check_longitude_range'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id')
    )
    op.create_index('ix_venues_coordinates', 'venues', ['latitude', 'longitude'])

    # Create offers table
    op.create_table(
        'offers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('items', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('status', postgresql.ENUM('DRAFT', 'ACTIVE', 'PAUSED', 'EXPIRED', 'SOLD_OUT', name='offerstatus', create_type=False), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('start_time < end_time', name='check_time_range'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_offers_business_id', 'offers', ['business_id'])
    op.create_index('ix_offers_status', 'offers', ['status'])
    op.create_index('ix_offers_start_time', 'offers', ['start_time'])
    op.create_index('ix_offers_end_time', 'offers', ['end_time'])
    op.create_index('ix_offers_created_at', 'offers', ['created_at'])
    op.create_index('ix_offers_status_end_time', 'offers', ['status', 'end_time'])
    op.create_index('ix_offers_business_status', 'offers', ['business_id', 'status'])

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customers_telegram_id', 'customers', ['telegram_id'], unique=True)

    # Create purchases table
    op.create_table(
        'purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('offer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('item_selections', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'CONFIRMED', 'CANCELED', name='purchasestatus', create_type=False), nullable=False),
        sa.Column('payment_provider', postgresql.ENUM('STRIPE', name='paymentprovider', create_type=False), nullable=True),
        sa.Column('payment_session_id', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('total_amount > 0', name='check_positive_total'),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_purchases_offer_id', 'purchases', ['offer_id'])
    op.create_index('ix_purchases_customer_id', 'purchases', ['customer_id'])
    op.create_index('ix_purchases_status', 'purchases', ['status'])
    op.create_index('ix_purchases_created_at', 'purchases', ['created_at'])
    op.create_index('ix_purchases_offer_status', 'purchases', ['offer_id', 'status'])


def downgrade() -> None:
    """Drop all tables and types."""
    op.drop_table('purchases')
    op.drop_table('customers')
    op.drop_table('offers')
    op.drop_table('venues')
    op.drop_table('businesses')
    
    op.execute('DROP TYPE IF EXISTS paymentprovider')
    op.execute('DROP TYPE IF EXISTS purchasestatus')
    op.execute('DROP TYPE IF EXISTS offerstatus')
    op.execute('DROP TYPE IF EXISTS verificationstatus')
