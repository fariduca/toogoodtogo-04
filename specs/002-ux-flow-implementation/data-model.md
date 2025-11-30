# Data Model: Telegram Marketplace Bot

**Feature**: 002-ux-flow-implementation  
**Date**: 2025-11-30  
**Purpose**: Define entities, relationships, state machines, and validation rules

---

## Core Entities

### 1. User

Represents any Telegram bot user (business owner or customer).

**Attributes**:
- `id` (PK): Integer - Auto-increment primary key
- `telegram_user_id`: BigInteger - Telegram user ID (unique, indexed)
- `telegram_username`: String(nullable) - Telegram @username
- `role`: Enum['BUSINESS', 'CUSTOMER'] - User role
- `language_code`: String(2) - ISO 639-1 language code (default: 'en')
- `notification_enabled`: Boolean - Whether user receives notifications (default: true)
- `last_location_lat`: Numeric(9,6, nullable) - Last shared location latitude
- `last_location_lon`: Numeric(9,6, nullable) - Last shared location longitude
- `last_location_updated`: Timestamp(nullable) - When location was last updated
- `created_at`: Timestamp - Registration timestamp
- `updated_at`: Timestamp - Last modification timestamp

**Relationships**:
- One User → Many Businesses (as owner)
- One User → Many Purchases (as customer)

**Indexes**:
- Unique index on `telegram_user_id`
- Index on `role` for filtered queries

**Validation Rules**:
- `telegram_user_id` must be positive integer
- `role` must be 'BUSINESS' or 'CUSTOMER'
- `language_code` must match ISO 639-1 (2-letter codes)

---

### 2. Business

Represents a registered business/venue that can post offers.

**Attributes**:
- `id` (PK): UUID - Unique business identifier
- `owner_id` (FK): Integer → User.id - Business owner
- `business_name`: String(200) - Business name
- `street_address`: String(200) - Street and number
- `city`: String(100) - City name
- `postal_code`: String(20) - Postal/ZIP code
- `country_code`: String(2) - ISO 3166-1 alpha-2 country code (default: 'FI')
- `latitude`: Numeric(9,6, nullable) - Geocoded latitude
- `longitude`: Numeric(9,6, nullable) - Geocoded longitude
- `contact_phone`: String(20, nullable) - Optional contact phone
- `logo_url`: String(500, nullable) - Azure Blob URL for logo
- `verification_status`: Enum['PENDING', 'APPROVED', 'REJECTED'] - Admin approval status
- `verification_notes`: Text(nullable) - Admin notes on verification
- `verified_at`: Timestamp(nullable) - When business was approved
- `verified_by`: Integer(nullable) - Admin user ID who verified
- `created_at`: Timestamp - Registration timestamp
- `updated_at`: Timestamp - Last modification timestamp

**Relationships**:
- Many Businesses → One User (owner)
- One Business → Many Offers

**Indexes**:
- Index on `owner_id` for user's businesses query
- Index on `verification_status` for admin approval queue
- Composite index on `(latitude, longitude)` for geospatial queries
- Unique index on `(business_name, postal_code)` to prevent duplicates

**Validation Rules**:
- `business_name` required, 3-200 characters
- `street_address` required, non-empty
- `city` required, non-empty
- `postal_code` required, matches country format
- `country_code` must be valid ISO 3166-1 alpha-2
- `contact_phone` must match E.164 format if provided
- `logo_url` must be valid HTTPS URL if provided

**State Machine**:

```
[Registration] → PENDING → [Admin Review] → APPROVED | REJECTED
                                              ↓
                                        [Can Post Offers]
```

---

### 3. Offer

Represents a deal posted by a business for excess produce.

**Attributes**:
- `id` (PK): UUID - Unique offer identifier
- `business_id` (FK): UUID → Business.id - Offering business
- `title`: String(100) - Offer title
- `description`: Text - Offer description (max 200 chars enforced at app level)
- `photo_url`: String(500, nullable) - Azure Blob URL for offer photo
- `category`: Enum(nullable) - ['MEALS', 'BAKERY', 'PRODUCE', 'OTHER'] - Offer category
- `price_per_unit`: Numeric(10,2) - Price in EUR (or configured currency)
- `currency`: String(3) - ISO 4217 currency code (default: 'EUR')
- `quantity_total`: Integer - Total units available at creation
- `quantity_remaining`: Integer - Current available units
- `pickup_start_time`: Timestamp - When pickup window opens
- `pickup_end_time`: Timestamp - When pickup window closes (and offer expires)
- `state`: Enum - ['ACTIVE', 'PAUSED', 'EXPIRED', 'EXPIRED_EARLY', 'SOLD_OUT'] - Offer state
- `created_at`: Timestamp - Creation timestamp
- `published_at`: Timestamp(nullable) - When offer became ACTIVE
- `updated_at`: Timestamp - Last modification timestamp

**Relationships**:
- Many Offers → One Business
- One Offer → Many Reservations

**Indexes**:
- Index on `business_id` for business's offers query
- Composite index on `(state, pickup_end_time)` for expiration job
- Composite index on `(state, created_at DESC)` for browse query
- Index on `category` for filtered discovery

**Validation Rules**:
- `title` required, 3-100 characters
- `description` required, 10-200 characters
- `price_per_unit` must be > 0, max 2 decimal places
- `quantity_total` must be > 0, integer
- `quantity_remaining` must be >= 0 and <= `quantity_total`
- `pickup_start_time` must be < `pickup_end_time`
- `pickup_end_time` must be in the future at creation
- `pickup_end_time` - `pickup_start_time` must be <= 24 hours (same-day or next-day only)

**State Machine**:

```
[Draft] → [Validation] → ACTIVE → EXPIRED (time-based)
                          ↓         ↓
                        PAUSED → EXPIRED_EARLY (manual)
                          ↓
                       SOLD_OUT (quantity = 0)

State Transitions:
- ACTIVE → PAUSED: Business taps "Pause"
- PAUSED → ACTIVE: Business taps "Resume" (only if before end_time)
- ACTIVE/PAUSED → SOLD_OUT: quantity_remaining reaches 0
- ACTIVE/PAUSED → EXPIRED: pickup_end_time <= now (automatic, 1-min check)
- ACTIVE/PAUSED → EXPIRED_EARLY: Business taps "End now"
- SOLD_OUT/EXPIRED/EXPIRED_EARLY: Terminal states (no further transitions)
```

**Computed Fields** (not stored):
- `available_for_reservation`: Boolean = `state == 'ACTIVE' AND quantity_remaining > 0 AND pickup_end_time > now()`
- `time_remaining`: Duration = `pickup_end_time - now()` (for "Ending soon" filter)

---

### 4. Reservation

Represents a customer's reservation for on-site payment at pickup.

**Attributes**:
- `id` (PK): UUID - Unique reservation identifier
- `order_id`: String(12, unique) - Customer-facing order ID (e.g., "RES-A3F2B8C1")
- `offer_id` (FK): UUID → Offer.id - Reserved offer
- `customer_id` (FK): Integer → User.id - Customer who reserved
- `quantity`: Integer - Number of units reserved
- `unit_price`: Numeric(10,2) - Price per unit at reservation time (snapshot)
- `total_price`: Numeric(10,2) - Total amount to pay on-site (quantity × unit_price)
- `currency`: String(3) - Currency code (copied from offer)
- `status`: Enum - ['CONFIRMED', 'CANCELLED'] - Reservation status
- `pickup_start_time`: Timestamp - Pickup window start (copied from offer)
- `pickup_end_time`: Timestamp - Pickup window end (copied from offer)
- `cancellation_reason`: Text(nullable) - Why reservation was cancelled (if applicable)
- `cancelled_at`: Timestamp(nullable) - When reservation was cancelled
- `created_at`: Timestamp - Reservation timestamp
- `updated_at`: Timestamp - Last modification timestamp

**Relationships**:
- Many Reservations → One Offer
- Many Reservations → One User (customer)

**Indexes**:
- Index on `offer_id` for offer's reservations query
- Index on `customer_id` for user's reservation history
- Index on `status` for filtering active/cancelled reservations
- Index on `order_id` for lookup at pickup (unique constraint)
- Composite index on `(customer_id, created_at DESC)` for reservation list

**Validation Rules**:
- `quantity` must be > 0, integer
- `unit_price` must be > 0, match offer price at creation
- `total_price` must equal `quantity × unit_price`
- `pickup_start_time` and `pickup_end_time` must match offer values at creation
- `order_id` must be unique and cryptographically random
- `status` transitions must follow state machine rules

**State Machine**:

```
[Reserve] → CONFIRMED
              ↓ (before pickup_end)
           CANCELLED
              ↓
        [Return units to inventory]

State Transitions:
- [Reserve] → CONFIRMED: Customer confirms reservation, inventory immediately decremented
- CONFIRMED → CANCELLED: Customer cancels before pickup_end_time, units returned to offer.quantity_remaining

Notes:
- No "PENDING" or "RESERVED" intermediate states - reservation is immediate
- No automatic expiration - customer must manually cancel via /my_reservations
- No payment tracking fields - payment happens on-site outside the system
- If customer doesn't show up (no-show), reservation stays CONFIRMED and inventory stays decremented
  (businesses handle no-shows manually)
```

**Immutable After Confirmation**:
- Once `status = 'CONFIRMED'`, the following fields are frozen:
  - `quantity`, `unit_price`, `total_price`
  - `pickup_start_time`, `pickup_end_time`
  - Offer snapshot preserved for auditing (even if offer later deleted)

---

## Relationships Diagram

```
User (BUSINESS)
  ↓ (1:N owner)
Business
  ↓ (1:N)
Offer
  ↓ (1:N)
Purchase
  ↓ (N:1 customer)
User (CUSTOMER)
```

**Cardinality**:
- One User (BUSINESS role) can own multiple Businesses (edge case: chains)
- One Business posts multiple Offers over time
- One Offer can have multiple Purchases (until sold out)
- One User (CUSTOMER role) can make multiple Purchases

**Cascade Rules**:
- Delete User → Soft delete Businesses (mark inactive, preserve audit trail)
- Delete Business → Soft delete Offers (mark unpublished, preserve purchases)
- Delete Offer → **Prohibited** if any CONFIRMED purchases exist (audit requirement)
- Delete User (customer) → Anonymize Purchases (replace with "Deleted User")

---

## Validation Rules Summary

### Field-Level Constraints

| Entity | Field | Rule |
|--------|-------|------|
| User | telegram_user_id | Positive BigInteger, unique |
| User | role | Must be 'BUSINESS' or 'CUSTOMER' |
| Business | business_name | 3-200 chars, required |
| Business | postal_code | Country-specific format validation |
| Business | logo_url | Valid HTTPS URL or null |
| Offer | title | 3-100 chars |
| Offer | description | 10-200 chars |
| Offer | price_per_unit | > 0, max 2 decimals |
| Offer | quantity_total | > 0, integer |
| Offer | pickup_end_time | Must be future at creation |
| Reservation | quantity | > 0, <= offer.quantity_remaining at reservation |
| Reservation | total_price | Must equal quantity × unit_price |

### Business Logic Constraints

1. **Offer Creation**: Business must have `verification_status = 'APPROVED'`
2. **Offer State Transition**: Only valid state machine transitions allowed
3. **Reservation Creation**: Offer must be `state = 'ACTIVE'` and `quantity_remaining >= quantity`
4. **Reservation Atomicity**: Use Redis SETNX to prevent overselling
5. **Cancellation Policy**: Reservation can only be cancelled if `now() < pickup_end_time`
6. **Inventory Consistency**: `offer.quantity_remaining` must equal `offer.quantity_total - SUM(confirmed_reservation.quantity)`

---

## Database Schema Evolution

### Alembic Migrations Required

**Migration 001**: Add geolocation columns to Business
```sql
ALTER TABLE businesses 
ADD COLUMN latitude NUMERIC(9, 6),
ADD COLUMN longitude NUMERIC(9, 6);

CREATE INDEX idx_businesses_location ON businesses(latitude, longitude);
```

**Migration 002**: Add last_location to User
```sql
ALTER TABLE users
ADD COLUMN last_location_lat NUMERIC(9, 6),
ADD COLUMN last_location_lon NUMERIC(9, 6),
ADD COLUMN last_location_updated TIMESTAMP;
```

**Migration 003**: Add order_id to Reservation (replaces Stripe fields)
```sql
ALTER TABLE reservations
ADD COLUMN order_id VARCHAR(12) UNIQUE NOT NULL;

CREATE UNIQUE INDEX idx_reservations_order_id ON reservations(order_id);
```

**Migration 004**: Extend offer states (if not already)
```sql
-- Ensure OfferState enum includes all required states
ALTER TYPE offerstate ADD VALUE IF NOT EXISTS 'EXPIRED_EARLY';
ALTER TYPE offerstate ADD VALUE IF NOT EXISTS 'SOLD_OUT';
```

---

## Redis Data Structures

### Offer Lock Keys (Transactional)

**Pattern**: `tmkt:lock:offer:{offer_id}`  
**Value**: "1" (dummy value)  
**TTL**: 5 seconds (short lock during reservation transaction only)

**Example**:
```redis
SET tmkt:lock:offer:uuid-123 "1" EX 5 NX
```

**Purpose**: Prevent race conditions when multiple customers simultaneously reserve the last unit. Lock is acquired, inventory checked/decremented, reservation created, then lock released - all within ~200ms.

**No Long-Duration Reservation Keys Needed**: With on-site payment model, reservations immediately decrement inventory (no temporary holds requiring TTL monitoring).

### Rate Limiting Keys

**Pattern**: `rate_limit:{user_id}:{command}`  
**Value**: Request count  
**TTL**: 60 seconds (sliding window)

**Example**:
```redis
INCR rate_limit:12345:/browse
EXPIRE rate_limit:12345:/browse 60
```

---

## Data Consistency Guarantees

### Atomicity

1. **Reservation Creation** (Simplified):
   - Acquire Redis lock on offer (`SETNX tmkt:lock:offer:{id}` with 5s TTL)
   - Within database transaction:
     - Check `offer.quantity_remaining >= requested_qty`
     - If insufficient → Rollback, return "sold out" error
     - Decrement `offer.quantity_remaining` by `requested_qty`
     - Create Reservation record with `status='CONFIRMED'`
     - Generate unique `order_id`
   - Release Redis lock (automatic on context exit)
   - Return success with order_id and pickup details

2. **Cancellation**:
   - Check `status = 'CONFIRMED' AND now() < pickup_end_time`
   - Within database transaction:
     - Update Reservation `status` to 'CANCELLED'
     - Increment `offer.quantity_remaining` by `quantity`
   - Return confirmation to customer

### Idempotency

- **Reservation Creation**: If customer taps "Reserve" button multiple times rapidly, Redis lock ensures only one reservation succeeds
- **Expiration Job**: Use `state` filter to avoid re-expiring already expired offers
- **Cancellation**: Check current status before updating (no-op if already cancelled)

### Data Integrity

- **No Partial Updates**: Database transactions ensure offer decrement and reservation creation happen together or not at all
- **No Orphaned Redis Keys**: Locks use TTL and auto-expire (no manual cleanup needed)
- **No Payment Reconciliation**: Since payment is on-site, no need to sync with external payment provider state

---

## Performance Considerations

### Indexes

**Critical for Query Performance**:
- `offers(state, pickup_end_time)` → Expiration job query
- `offers(state, created_at DESC)` → Browse query with pagination
- `businesses(latitude, longitude)` → Geospatial filtering (may upgrade to PostGIS)
- `reservations(customer_id, created_at DESC)` → Customer reservation history

**Index Maintenance**:
- `ANALYZE` tables weekly to update statistics
- Monitor index bloat on high-write tables (offers, purchases)

### Query Optimization

1. **Browse Query** (customers):
   ```sql
   SELECT * FROM offers
   WHERE state = 'ACTIVE' 
     AND quantity_remaining > 0
     AND pickup_end_time > NOW()
   ORDER BY created_at DESC
   LIMIT 10;
   ```
   - Uses composite index `(state, created_at DESC)`
   - Geolocation filter applied in application layer (Haversine formula)

2. **Expiration Query** (background job):
   ```sql
   SELECT id, business_id FROM offers
   WHERE state = 'ACTIVE'
     AND pickup_end_time <= NOW();
   ```
   - Uses composite index `(state, pickup_end_time)`
   - Returns minimal columns for update

3. **Inventory Check** (purchase):
   ```sql
   SELECT quantity_remaining FROM offers
   WHERE id = ? AND state = 'ACTIVE'
   FOR UPDATE;  -- Row-level lock for atomic decrement
   ```

### Caching Strategy

- **Business Details**: Cache in Redis for 1 hour (rarely changes)
- **Offer Details**: No caching (real-time inventory critical)
- **User Profiles**: Cache for 5 minutes (role, preferences)
- **Geocoding Results**: Cache lat/lng in Business record (permanent)

---

## Audit and Logging Events (FR-030)

### Structured Log Events

**Offer Lifecycle**:
- `offer.created`: {offer_id, business_id, title, quantity, price}
- `offer.published`: {offer_id, pickup_start, pickup_end}
- `offer.paused`: {offer_id, business_id, reason}
- `offer.resumed`: {offer_id, business_id}
- `offer.expired`: {offer_id, expiration_type: 'auto' | 'manual'}
- `offer.sold_out`: {offer_id, final_quantity_sold}

**Purchase Lifecycle**:
- `reservation.created`: {reservation_id, offer_id, customer_id, quantity}
- `reservation.confirmed`: {reservation_id, offer_id, timestamp}
- `reservation.cancelled`: {reservation_id, reason}

**Inventory Changes**:
- `inventory.decremented`: {offer_id, old_quantity, new_quantity, trigger: 'purchase' | 'edit'}
- `inventory.incremented`: {offer_id, old_quantity, new_quantity, trigger: 'cancellation' | 'edit'}

**Errors**:
- `reservation.race_condition`: {offer_id, attempted_quantity, available_quantity}
- `expiration.job_failed`: {error_message, offers_processed}

**Security Events**:
- `auth.permission_denied`: {user_id, attempted_action, required_role}
- `rate_limit.exceeded`: {user_id, command, limit}

---

## Next Steps

1. **Implement ORM Models**: Create SQLAlchemy models matching this schema
2. **Write Alembic Migrations**: Evolve existing schema with new columns
3. **Define Pydantic DTOs**: Input/output validation models for handlers
4. **Create Repository Methods**: CRUD operations with proper error handling
5. **Write Unit Tests**: Model validation, state machine transitions, business rules

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-30  
**Related**: [research.md](./research.md), [spec.md](./spec.md)
