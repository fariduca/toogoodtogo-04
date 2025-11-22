# Data Model: Telegram Marketplace

Date: 2025-11-13

## Entities

### Business
Fields:
- id (UUID)
- name (String, 3-100 chars)
- venue_id (FK -> Venue)
- contact_handle (String, Telegram username or phone reference)
- verification_status (Enum: pending, approved, rejected)
- created_at (Timestamp)
- updated_at (Timestamp)
Validation:
- name required, unique per venue
- contact_handle required
State Transitions:
- pending -> approved (manual admin action)
- pending -> rejected (admin action)

### Venue
Fields:
- id (UUID)
- address_line1 (String)
- address_line2 (String, optional)
- city (String)
- postal_code (String)
- country (String, ISO code)
- geo_lat (Decimal, optional)
- geo_lng (Decimal, optional)
Validation:
- address_line1, city, postal_code, country required
- geo coords optional, both must be present if one provided

### Offer
Fields:
- id (UUID)
- business_id (FK -> Business)
- title (String, 5-120 chars)
- description (Text, optional)
- items (Array<Item>)
- start_time (Timestamp)
- end_time (Timestamp)
- status (Enum: draft, active, paused, expired, sold_out)
- image_url (String, optional)
- created_at (Timestamp)
- updated_at (Timestamp)
Validation:
- title required
- start_time < end_time
- items length >= 1
State Transitions:
- draft -> active (publish criteria met)
- active -> paused (business action)
- active -> expired (auto via scheduler at end_time)
- active|paused -> sold_out (quantity zero across all items)

### Item (Value Object inside Offer)
Fields:
- name (String, 2-80 chars)
- unit_price (Decimal >= 0)
- quantity_available (Integer >= 0)
Validation:
- name required
- quantity_available >= 0

### Purchase
Fields:
- id (UUID)
- offer_id (FK -> Offer)
- customer_id (FK -> Customer)
- item_selections (Array<PurchaseItem>)
- total_amount (Decimal)
- payment_provider (Enum: stripe)
- payment_reference (String)
- status (Enum: pending, confirmed, canceled)
- created_at (Timestamp)
Validation:
- total_amount == sum(item_selections quantities * unit_price)
State Transitions:
- pending -> confirmed (after successful external checkout)
- pending -> canceled (user cancellation before end_time)

### PurchaseItem (Value Object inside Purchase)
Fields:
- item_name (String)
- quantity (Integer > 0)
- unit_price (Decimal >= 0)

### Customer
Fields:
- id (UUID)
- telegram_handle (String)
- created_at (Timestamp)
Validation:
- handle required

## Relationships
- Business 1..1 Venue
- Business 1..* Offer
- Offer 1..* Item (value objects)
- Offer 1..* Purchase (through Purchase records)
- Purchase 1..* PurchaseItem (value objects)
- Customer 1..* Purchase

## Derived / Computed Fields
- Offer.remaining_quantity = sum(items.quantity_available) - sum(purchase confirmed quantities)
- Offer.popularity_score = confirmed_purchase_count (MVP)

## Indexing Considerations
- Offer: (status, end_time) for pruning/query
- Purchase: (offer_id, status)
- Business: (verification_status)

## Validation Rules Summary
- Prevent purchase if Offer.status not active
- Prevent overselling: atomic decrement via Redis lock
- Expire offers via scheduled job scanning end_time <= now AND status=active

## State Diagram Notes
- Overselling prevention: lock on Offer.id during purchase computation
- Sold_out determined after inventory update; triggers status transition

