"""Add users table and update schema for reservation model

Revision ID: 002_ux_flow_implementation
Revises: 001_initial_schema
Create Date: 2025-11-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_ux_flow_implementation'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate to reservation-based model with users table."""
    
    # Create new enum types
    op.execute("CREATE TYPE userrole AS ENUM ('BUSINESS', 'CUSTOMER')")
    op.execute("CREATE TYPE reservationstatus AS ENUM ('CONFIRMED', 'CANCELLED')")
    op.execute("CREATE TYPE offercategory AS ENUM ('MEALS', 'BAKERY', 'PRODUCE', 'OTHER')")
    
    # Update existing enum types
    op.execute("ALTER TYPE verificationstatus RENAME TO verificationstatus_old")
    op.execute("CREATE TYPE verificationstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED')")
    op.execute("ALTER TABLE businesses ALTER COLUMN verification_status TYPE verificationstatus USING verification_status::text::verificationstatus")
    op.execute("DROP TYPE verificationstatus_old")
    
    op.execute("ALTER TYPE offerstatus RENAME TO offerstatus_old")
    op.execute("CREATE TYPE offerstatus AS ENUM ('ACTIVE', 'PAUSED', 'EXPIRED', 'EXPIRED_EARLY', 'SOLD_OUT')")
    op.execute("ALTER TABLE offers ALTER COLUMN status TYPE offerstatus USING CASE WHEN status::text = 'DRAFT' THEN 'ACTIVE' ELSE status::text END::offerstatus")
    op.execute("DROP TYPE offerstatus_old")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_username', sa.String(length=100), nullable=True),
        sa.Column('role', postgresql.ENUM('BUSINESS', 'CUSTOMER', name='userrole', create_type=False), nullable=False),
        sa.Column('language_code', sa.String(length=2), nullable=False, server_default='en'),
        sa.Column('notification_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_location_lat', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('last_location_lon', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('last_location_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_telegram_user_id', 'users', ['telegram_user_id'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])
    
    # Drop venues table and merge into businesses
    op.drop_table('venues')
    
    # Update businesses table
    op.add_column('businesses', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('businesses', sa.Column('business_name', sa.String(length=200), nullable=True))
    op.add_column('businesses', sa.Column('street_address', sa.String(length=200), nullable=True))
    op.add_column('businesses', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('businesses', sa.Column('postal_code', sa.String(length=20), nullable=True))
    op.add_column('businesses', sa.Column('country_code', sa.String(length=2), nullable=False, server_default='FI'))
    op.add_column('businesses', sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column('businesses', sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column('businesses', sa.Column('contact_phone', sa.String(length=20), nullable=True))
    op.add_column('businesses', sa.Column('logo_url', sa.String(length=500), nullable=True))
    op.add_column('businesses', sa.Column('verification_notes', sa.Text(), nullable=True))
    op.add_column('businesses', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.add_column('businesses', sa.Column('verified_by', sa.Integer(), nullable=True))
    
    # Migrate existing data (rename name to business_name, telegram_id -> owner_id via users table)
    # Note: This requires manual data migration for existing data
    op.execute("""
        UPDATE businesses SET 
            business_name = name,
            street_address = 'Migration required',
            city = 'Migration required',
            postal_code = '00000'
    """)
    
    # Drop old columns from businesses
    op.drop_column('businesses', 'name')
    op.drop_column('businesses', 'telegram_id')
    op.drop_column('businesses', 'photo_url')
    
    # Make new columns non-nullable after migration
    op.alter_column('businesses', 'business_name', nullable=False)
    op.alter_column('businesses', 'street_address', nullable=False)
    op.alter_column('businesses', 'city', nullable=False)
    op.alter_column('businesses', 'postal_code', nullable=False)
    op.alter_column('businesses', 'owner_id', nullable=False)
    
    # Add foreign key for owner_id
    op.create_foreign_key('fk_businesses_owner_id', 'businesses', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    
    # Create new indexes for businesses
    op.create_index('ix_businesses_owner_id', 'businesses', ['owner_id'])
    op.create_index('ix_businesses_location', 'businesses', ['latitude', 'longitude'])
    op.create_index('ix_businesses_name_postal', 'businesses', ['business_name', 'postal_code'], unique=True)
    
    # Update offers table
    op.add_column('offers', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('offers', sa.Column('photo_url', sa.String(length=500), nullable=True))
    op.add_column('offers', sa.Column('category', postgresql.ENUM('MEALS', 'BAKERY', 'PRODUCE', 'OTHER', name='offercategory', create_type=False), nullable=True))
    op.add_column('offers', sa.Column('price_per_unit', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('offers', sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'))
    op.add_column('offers', sa.Column('quantity_total', sa.Integer(), nullable=True))
    op.add_column('offers', sa.Column('quantity_remaining', sa.Integer(), nullable=True))
    op.add_column('offers', sa.Column('pickup_start_time', sa.DateTime(), nullable=True))
    op.add_column('offers', sa.Column('pickup_end_time', sa.DateTime(), nullable=True))
    op.add_column('offers', sa.Column('state', postgresql.ENUM('ACTIVE', 'PAUSED', 'EXPIRED', 'EXPIRED_EARLY', 'SOLD_OUT', name='offerstatus', create_type=False), nullable=True))
    op.add_column('offers', sa.Column('published_at', sa.DateTime(), nullable=True))
    
    # Migrate existing offer data
    op.execute("""
        UPDATE offers SET 
            description = 'Migration required',
            price_per_unit = 10.00,
            quantity_total = 1,
            quantity_remaining = 1,
            pickup_start_time = start_time,
            pickup_end_time = end_time,
            state = status::text::offerstatus
    """)
    
    # Drop old offer columns
    op.drop_column('offers', 'items')
    op.drop_column('offers', 'start_time')
    op.drop_column('offers', 'end_time')
    op.drop_column('offers', 'status')
    op.drop_column('offers', 'image_url')
    
    # Make new columns non-nullable
    op.alter_column('offers', 'description', nullable=False)
    op.alter_column('offers', 'price_per_unit', nullable=False)
    op.alter_column('offers', 'quantity_total', nullable=False)
    op.alter_column('offers', 'quantity_remaining', nullable=False)
    op.alter_column('offers', 'pickup_start_time', nullable=False)
    op.alter_column('offers', 'pickup_end_time', nullable=False)
    op.alter_column('offers', 'state', nullable=False)
    
    # Add check constraints for offers
    op.create_check_constraint('check_positive_price', 'offers', 'price_per_unit > 0')
    op.create_check_constraint('check_positive_total_quantity', 'offers', 'quantity_total > 0')
    op.create_check_constraint('check_nonnegative_remaining', 'offers', 'quantity_remaining >= 0')
    op.create_check_constraint('check_remaining_le_total', 'offers', 'quantity_remaining <= quantity_total')
    
    # Update offer indexes
    op.create_index('ix_offers_state_pickup_end', 'offers', ['state', 'pickup_end_time'])
    op.create_index('ix_offers_state_created', 'offers', ['state', sa.text('created_at DESC')])
    op.create_index('ix_offers_business_state', 'offers', ['business_id', 'state'])
    op.create_index('ix_offers_category', 'offers', ['category'])
    
    # Drop purchases and customers tables
    op.drop_table('purchases')
    op.drop_table('customers')
    
    # Drop old enum types
    op.execute("DROP TYPE IF EXISTS purchasestatus")
    op.execute("DROP TYPE IF EXISTS paymentprovider")
    
    # Create reservations table
    op.create_table(
        'reservations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('order_id', sa.String(length=12), nullable=False),
        sa.Column('offer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('status', postgresql.ENUM('CONFIRMED', 'CANCELLED', name='reservationstatus', create_type=False), nullable=False, server_default='CONFIRMED'),
        sa.Column('pickup_start_time', sa.DateTime(), nullable=False),
        sa.Column('pickup_end_time', sa.DateTime(), nullable=False),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('quantity > 0', name='check_positive_quantity'),
        sa.CheckConstraint('unit_price > 0', name='check_positive_unit_price'),
        sa.CheckConstraint('total_price > 0', name='check_positive_total_price'),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reservations_offer_id', 'reservations', ['offer_id'])
    op.create_index('ix_reservations_customer_id', 'reservations', ['customer_id'])
    op.create_index('ix_reservations_order_id', 'reservations', ['order_id'], unique=True)
    op.create_index('ix_reservations_customer_created', 'reservations', ['customer_id', sa.text('created_at DESC')])
    op.create_index('ix_reservations_status', 'reservations', ['status'])
    op.create_index('ix_reservations_created_at', 'reservations', ['created_at'])


def downgrade() -> None:
    """Revert to previous schema."""
    # Drop new tables
    op.drop_table('reservations')
    op.drop_table('users')
    
    # Drop new enum types
    op.execute("DROP TYPE IF EXISTS reservationstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS offercategory")
    
    # Note: Full downgrade would require restoring old schema
    # This is a simplified downgrade that removes new structures
    # Full restoration would need more complex migration logic
