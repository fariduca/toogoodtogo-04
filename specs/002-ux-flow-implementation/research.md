# Technical Research: UX Flow Implementation

**Feature Branch**: `002-ux-flow-implementation`  
**Created**: 2025-11-30  
**Updated**: 2025-11-30 (Payment model changed to on-site)  
**Purpose**: Document technical decisions for implementing the Telegram marketplace bot UX flow

---

## 1. Reservation Flow (On-Site Payment Model)

### Decision

**Implement immediate reservation system with on-site payment** - no payment provider integration.

### Rationale

1. **Simplified MVP**: Removes payment provider integration complexity (Stripe API, webhooks, PCI compliance), allowing faster implementation and testing of core marketplace functionality.

2. **Lower Operational Overhead**: No payment processing fees, no webhook infrastructure to maintain, no payment provider account requirements for businesses.

3. **Flexibility for Businesses**: Businesses can accept cash, card terminal payments, or any method they prefer without being locked into a specific payment processor.

4. **Faster Time to Market**: Removing external payment dependency eliminates a major integration risk and reduces development time by ~40%.

5. **Reduced Error Surface**: No payment failures, network timeouts, or webhook processing failures to handle - reservation either succeeds or fails based purely on inventory availability.

### How It Works

**Core Flow**:
1. Customer selects offer and quantity → Bot validates inventory availability
2. Customer taps "Reserve" → Bot shows confirmation: "Reserve [X] items for [Total]? Payment on-site at pickup."
3. Customer confirms → Bot immediately:
   - Creates reservation record with `CONFIRMED` status
   - Decrements `offer.quantity_remaining` (permanent, not temporary)
   - Generates unique order ID
4. Bot sends confirmation message with:
   - Order ID (for pickup verification)
   - Business name and full address
   - Pickup time window
   - Total amount to pay: "Pay [amount] on-site when you pick up"
5. Customer shows up during pickup window and pays business directly
6. Business verifies order ID and provides items

**Reservation Lifecycle**:
- **CONFIRMED**: Active reservation, inventory decremented
- **CANCELLED**: Customer cancelled via `/my_reservations` → inventory returned
- **NO_SHOW** (implicit): If customer doesn't show up, reservation stays CONFIRMED and inventory stays decremented (business handles no-shows manually)

### Alternatives Considered

**Telegram Payments + Stripe (original plan)**
- **Pros**: Guaranteed payment upfront, automated refund handling, professional checkout experience
- **Cons**: 
  - Complex integration (Stripe API, webhook handling, signature verification)
  - Payment processing fees reduce business margins
  - Requires PCI compliance considerations
  - Adds significant development time
  - Refund processing required for cancellations
- **Why Not Chosen**: Adds too much complexity for MVP. On-site payment delivers same core value (reserve expiring inventory) with 70% less code.

**Temporary Reservation with Auto-Release (5-minute hold)**
- **Pros**: Prevents "reservation abuse" where customers reserve without pickup intent
- **Cons**: 
  - Requires background job to monitor and release expired reservations
  - Adds complexity to inventory management
  - Customer confusion if reservation expires unexpectedly
  - Doesn't solve no-show problem anyway (same issue deferred to pickup time)
- **Why Not Chosen**: Simpler to decrement immediately and let businesses handle no-shows case-by-case. Most customers will honor reservations.

### Implementation Notes

**Database Schema**:
```python
class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(UUID, primary_key=True)
    order_id = Column(String(12), unique=True, nullable=False)  # e.g., "RES-ABC123XY"
    offer_id = Column(UUID, ForeignKey("offers.id"), nullable=False)
    customer_id = Column(BigInteger, nullable=False)  # Telegram user ID
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum("CONFIRMED", "CANCELLED"), nullable=False, default="CONFIRMED")
    created_at = Column(DateTime, nullable=False, default=func.now())
    cancelled_at = Column(DateTime, nullable=True)
```

**No Payment Fields Needed**:
- No `payment_intent_id`, `checkout_session_id`, `stripe_payment_status`
- No `refund_id` or refund tracking
- No webhook handling infrastructure

**Concurrency Control** (same as before):
- Use PostgreSQL row-level locking: `SELECT ... FOR UPDATE` on offer row
- Atomic inventory check and decrement in same transaction
- If `quantity_remaining < requested_quantity` → rollback and return "Sold out" error

**Order ID Generation**:
```python
import secrets
order_id = f"RES-{secrets.token_hex(4).upper()}"  # e.g., "RES-A3F2B8C1"
```

**Error Handling**:
- **Insufficient Inventory**: "That was the last unit and someone just reserved it. Try another deal!"
- **Offer Expired**: "This offer expired at [time]. Browse other deals with /browse"
- **Offer Paused**: "This offer is currently unavailable. Try another deal."

**Security Considerations**:
- **Rate Limiting**: Prevent customers from mass-reserving items to grief businesses
- **Order ID Uniqueness**: Ensure order IDs are cryptographically random to prevent guessing
- **Cancellation Abuse**: Monitor customers who repeatedly reserve and cancel (future enhancement)

**Testing Strategy**:
1. **Unit Tests**: Reservation creation, inventory decrement, order ID generation
2. **Integration Tests**: Race condition handling (two customers reserving last unit)
3. **E2E Tests**: Full flow from `/browse` → reserve → confirmation → view in `/my_reservations`
4. **Load Tests**: Verify transactional integrity under concurrent reservations

### Migration from Existing Code

**Files to Modify**:
- `src/storage/db_models.py`: Rename `Purchase` → `Reservation`, remove payment fields
- `src/services/purchase_flow.py` → `src/services/reservation_flow.py`: Simplify logic, remove payment steps
- `src/handlers/purchasing/`: Update handlers to show "Reserve" button and confirmation flow
- Remove `src/services/stripe_checkout.py` (no longer needed)
- Remove webhook handler for Stripe events

**Preserved Logic**:
- Inventory reservation and race condition handling (already correct)
- Offer validation before reservation (already implemented)
- Reservation cancellation logic (just remove refund processing)

---

## 2. Geolocation Filtering (5km Radius)
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{self.success_url}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=self.cancel_url,
        metadata={"purchase_id": str(purchase_id)},
    )
    expires_at = datetime.utcnow() + timedelta(hours=24)
    return session.url, expires_at
```

**Gotchas**:
- Stripe amounts must be in cents (multiply by 100)
- `{CHECKOUT_SESSION_ID}` placeholder is auto-replaced by Stripe with actual session ID
- Metadata limited to 500 characters; store only essential data (purchase_id)
- Webhook endpoint must return 200 status quickly (< 5 seconds) or Stripe will retry

---

## 2. Geolocation Filtering (5km Radius)

### Decision

**Use Haversine formula for application-level distance calculation** with PostgreSQL storing coordinates as `NUMERIC(10,8)` and `NUMERIC(11,8)` for latitude/longitude.

Defer PostGIS spatial indexing to post-MVP optimization if performance becomes an issue.

### Rationale

1. **Simplicity**: Haversine is a well-established formula (single Python function) with no additional database extensions required.

2. **MVP Scope**: With expected offer volume (< 1000 active offers), filtering in application layer is performant enough (< 100ms for 1000 calculations).

3. **Database Compatibility**: Works with standard PostgreSQL without PostGIS extension, reducing deployment complexity.

4. **Geocoding Not Required Yet**: Businesses already provide coordinates during registration (`/register_business` flow prompts for location sharing or manual coordinates). No need for external geocoding API.

5. **Future Migration Path**: Schema already supports spatial columns; can add PostGIS and migrate to `geography` type later without schema changes.

### Alternatives Considered

**PostGIS with `geography` Type and Spatial Indexing**
- **Pros**: 
  - Native spatial queries (`ST_DWithin(location, user_location, 5000)`)
  - GiST/BRIN indexes for O(log n) lookups vs O(n) application filtering
  - Built-in distance functions (no manual Haversine implementation)
- **Cons**:
  - Requires PostGIS extension (additional deployment dependency)
  - More complex for MVP (install, configure, learn spatial SQL)
  - Overhead not justified for small dataset (< 1000 offers)
- **Why Not Chosen**: Premature optimization. Application-level filtering is sufficient for MVP and can be migrated later if needed.

**External Geocoding API (Google Maps, Mapbox, OpenStreetMap)**
- **Pros**: 
  - Convert user addresses to coordinates automatically
  - Reverse geocoding for display purposes ("123 Main St" → lat/lon)
- **Cons**:
  - Not needed: Telegram already provides coordinates via location sharing
  - Adds external API dependency (cost, rate limits, latency)
  - Address-to-coordinate conversion is one-time during registration, not query time
- **Why Not Chosen**: Telegram's native location sharing provides coordinates directly. Geocoding addresses is not required for MVP.

**S2 Geometry Library (Google's Spatial Library)**
- **Pros**: Cell-based spatial indexing, very efficient for large datasets
- **Cons**: Complex setup, overkill for MVP scale
- **Why Not Chosen**: Over-engineered for current requirements.

### Implementation Notes

**Database Schema** (already implemented in `scripts/alembic/versions/001_initial_schema.py`):
```python
# venues table
sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=False)
sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=False)
sa.CheckConstraint('latitude >= -90 AND latitude <= 90', name='check_latitude_range')
sa.CheckConstraint('longitude >= -180 AND longitude <= 180', name='check_longitude_range')

# Index for future spatial queries (not used in MVP)
op.create_index('ix_venues_coordinates', 'venues', ['latitude', 'longitude'])
```

**Haversine Formula Implementation**:
```python
# src/services/discovery_ranking.py (to be implemented)
import math

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    R = 6371  # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    return R * c  # Distance in km

async def filter_nearby_offers(
    offers: list[Offer], 
    user_lat: float, 
    user_lon: float, 
    radius_km: float = 5.0
) -> list[Offer]:
    """Filter offers within radius of user location."""
    nearby = []
    for offer in offers:
        # Fetch venue coordinates from business
        venue = await get_venue_for_business(offer.business_id)
        distance = calculate_distance_km(user_lat, user_lon, venue.latitude, venue.longitude)
        if distance <= radius_km:
            nearby.append(offer)
    return nearby
```

**Customer Browse Flow**:
1. Customer sends `/browse` with optional location sharing
2. Bot prompts: "Share your location for nearby deals, or see all deals" → Inline keyboard: `[Share Location]` `[All Deals]`
3. If location shared → Telegram sends `message.location` with `latitude`/`longitude`
4. Bot queries all active offers from database
5. Filter offers in Python using Haversine (distance ≤ 5km)
6. Sort by distance (closest first) + secondary sort by creation time
7. Display paginated results (5 offers per page)

**Performance Considerations**:
- **Expected Query Time**: ~50-100ms for 1000 offers (Python loop with math operations)
- **Optimization Threshold**: If > 5000 active offers, migrate to PostGIS with spatial index
- **Caching**: Consider Redis caching of offer coordinates (TTL 5 minutes) if query becomes bottleneck

**Future PostGIS Migration** (if needed):
```sql
-- Add PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Add geography column
ALTER TABLE venues ADD COLUMN location geography(POINT, 4326);

-- Populate from existing coordinates
UPDATE venues SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);

-- Add spatial index
CREATE INDEX idx_venues_location ON venues USING GIST(location);

-- Query within 5km radius
SELECT o.* FROM offers o
JOIN businesses b ON o.business_id = b.id
JOIN venues v ON b.id = v.business_id
WHERE ST_DWithin(v.location, ST_SetSRID(ST_MakePoint(:user_lon, :user_lat), 4326)::geography, 5000)
AND o.status = 'ACTIVE';
```

**Accuracy Notes**:
- Haversine assumes spherical Earth (accurate to ~0.5% error vs actual geodesic distance)
- For 5km radius, error is < 25 meters (acceptable for "nearby" filtering)
- Coordinates stored as `NUMERIC` preserve precision (8 decimal places = ~1mm accuracy)

**Testing Strategy**:
1. **Unit Test**: Verify Haversine calculation with known coordinates (e.g., NYC to SF = ~4,130 km)
2. **Integration Test**: Create offers at known distances (2km, 5km, 10km) from test user location; verify correct filtering
3. **Edge Cases**: Test offers at exactly 5.0km boundary, negative coordinates (southern/western hemisphere), prime meridian crossing

---

## 3. Redis-Based Reservation Locks

### Decision

**Use Redis `SETNX` (SET if Not eXists) with 5-minute TTL** for atomic inventory reservation locks during purchase flow.

Implement lock acquisition in `RedisLockHelper.acquire_offer_lock()` with context manager pattern for automatic release.

### Rationale

1. **Atomic Operations**: `SETNX` guarantees only one client can acquire lock, preventing race conditions when multiple customers purchase simultaneously.

2. **Automatic Expiry**: TTL ensures locks are released even if bot crashes or network fails (no orphaned locks).

3. **Simple Implementation**: Single Redis command (`SET key value NX EX ttl`) vs complex Redlock algorithm with multiple Redis instances.

4. **5-Minute TTL Matches Use Case**: Gives customer time to complete payment (Stripe checkout typically < 2 minutes) with buffer for slow connections.

5. **Already Implemented**: Codebase has `RedisLockHelper` (`src/storage/redis_locks.py`) using this pattern.

### Alternatives Considered

**Redlock Algorithm (Distributed Lock)**
- **Pros**: 
  - Higher reliability (survives single Redis node failure)
  - Guarantees lock safety across multiple Redis instances
- **Cons**:
  - Requires 3-5 Redis instances (higher infrastructure cost)
  - More complex implementation (retry logic, quorum checks)
  - Overkill for single-node MVP deployment
- **Why Not Chosen**: MVP runs single Redis instance; Redlock complexity not justified until high-availability deployment.

**PostgreSQL Advisory Locks**
- **Pros**: 
  - No additional infrastructure (uses existing database)
  - Automatic release on connection close
- **Cons**:
  - Locks tied to database connection (not HTTP request lifecycle)
  - Higher latency than Redis (network round-trip + disk I/O)
  - No TTL mechanism (manual cleanup required)
- **Why Not Chosen**: Redis is already deployed for rate limiting; advisory locks have awkward lifecycle management.

**Application-Level Mutex**
- **Pros**: Simple in-process lock (no external dependency)
- **Cons**:
  - Only works in single-process deployment (breaks with multiple bot instances)
  - No distributed coordination
## 3. Redis-Based Reservation Locks

### Decision

**Use Redis SETNX with short TTL (5 seconds) for atomic offer-level locks** during reservation creation to prevent race conditions.

**NO long-duration reservation holds** - reservations immediately decrement inventory permanently.

### Rationale

1. **Immediate Inventory Decrement**: With on-site payment model, reservations are final the moment customer confirms. No need for 5-minute temporary holds.

2. **Short Lock Duration**: Lock is only held during the atomic reservation transaction (~1-2 seconds max):
   - Check inventory availability
   - Create reservation record
   - Decrement `offer.quantity_remaining`
   - Generate order ID
   
3. **Prevents Overselling**: Redis SETNX ensures only one reservation operation can proceed per offer at a time, preventing race conditions when multiple customers reserve simultaneously.

4. **Existing Infrastructure**: Redis already deployed for rate limiting; adding locks requires no new dependencies.

5. **Automatic Cleanup**: Locks with TTL expire automatically if bot crashes mid-transaction (no orphaned locks).

### Alternatives Considered

**In-Memory Locks (Python `asyncio.Lock`)**
- **Pros**: No external dependency, zero latency
- **Cons**: 
  - Only works within single bot process
  - Doesn't support horizontal scaling (multiple bot instances)
  - Lost on bot restart
- **Why Not Chosen**: Architecture supports horizontal scaling (multiple bot instances); need distributed lock.

**Database Row-Level Locks (`SELECT ... FOR UPDATE`)**
- **Pros**: Native SQL feature, ACID guarantees
- **Cons**:
  - Holds transaction open during entire operation
  - Can block other queries
  - Connection pool concerns
- **Why Not Chosen**: Redis is faster for ephemeral locks; database handles persistence, not coordination.

**Long-Duration Reservation Holds (5-minute TTL, original plan)**
- **Pros**: Inventory returns if customer abandons without completing payment
- **Cons**:
  - Complex background job to monitor and release expired holds
  - Customer confusion if hold expires
  - Still doesn't prevent no-shows (same problem deferred)
  - Requires Redis keys per reservation with cleanup logic
- **Why Not Chosen**: On-site payment model makes this unnecessary - reservation is commitment, not tentative hold.

### Implementation Notes

**Lock Acquisition Pattern** (already implemented in `src/storage/redis_locks.py`):
```python
class RedisLockHelper:
    def __init__(self, redis_url: str, ttl_seconds: int = 5):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds  # 5 seconds - short lock for transaction only
        self._client: redis.Redis | None = None

    @asynccontextmanager
    async def acquire_offer_lock(self, offer_id: UUID) -> AsyncGenerator[bool, None]:
        """Acquire exclusive lock on offer for reservation operations."""
        if not self._client:
            raise RuntimeError("Redis client not connected")

        lock_key = f"tmkt:lock:offer:{offer_id}"
        acquired = False

        try:
            # Atomic lock acquisition with TTL
            acquired = await self._client.set(
                lock_key, "1", ex=self.ttl_seconds, nx=True
            )
            yield bool(acquired)
        finally:
            if acquired:
                await self._client.delete(lock_key)
```

**✅ Current implementation is CORRECT for on-site payment model** - 5-second TTL is appropriate for short transactional lock.

**Updated Usage (Simplified for Immediate Reservation)**:
```python
# Initialize with 5-second TTL for transactional locks
lock_helper = RedisLockHelper(redis_url=settings.redis_url, ttl_seconds=5)

# Reservation flow with immediate inventory decrement
async with lock_helper.acquire_offer_lock(offer_id) as lock_acquired:
    if not lock_acquired:
        return ReservationResult(success=False, error="Offer currently being reserved by another customer")
    
    # Check inventory
    offer = await offer_repo.get_by_id(offer_id)
    if offer.quantity_remaining < requested_qty:
        return ReservationResult(success=False, error="Insufficient quantity")
    
    # Decrement inventory atomically (permanent)
    await offer_repo.decrement_quantity(offer_id, requested_qty)
    
    # Create reservation record with CONFIRMED status
    reservation = await reservation_repo.create(
        offer_id=offer_id,
        customer_id=customer_id,
        quantity=requested_qty,
        total_price=offer.price_per_unit * requested_qty,
        status="CONFIRMED"
    )
    
    # Generate order ID
    order_id = f"RES-{secrets.token_hex(4).upper()}"
    
    # Lock auto-releases on context exit (1-2 seconds elapsed)
    return ReservationResult(success=True, reservation=reservation, order_id=order_id)
```

**Race Condition Prevention**:
1. **Customer A and B simultaneously reserve last item**:
   - Customer A acquires lock → Checks inventory (1 available) → Decrements to 0 → Creates reservation
   - Customer B tries to acquire lock → Waits/fails → Cannot proceed
   - **Result**: Only one reservation succeeds (correct behavior)

2. **Lock Expiry During Transaction**:
   - Lock TTL (5 seconds) is much longer than transaction time (~200ms)
   - If transaction somehow takes > 5 seconds (e.g., DB latency spike), lock expires but transaction still completes
   - **Risk**: Two concurrent transactions could both succeed if first is extremely slow
   - **Mitigation**: Use database transaction to ensure ACID guarantees (next section)

3. **Bot Crash After Decrement**:
   - Customer acquires lock → Decrements inventory → Bot crashes before creating reservation
   - Lock expires after 5 seconds → Inventory stays decremented (data loss - units lost)
   - **Mitigation**: Use database transaction to roll back decrement if reservation creation fails

**Improved Transactional Pattern with Database ACID**:
```python
async with db.session() as session:
    async with lock_helper.acquire_offer_lock(offer_id) as lock_acquired:
        if not lock_acquired:
            return ReservationResult(success=False, error="Offer locked")
        
        # All DB operations in single transaction
        offer = await offer_repo.get_by_id(offer_id, session=session)
        
        if offer.quantity_remaining < requested_qty:
            raise ValueError("Insufficient quantity")
        
        # Decrement and create reservation atomically
        await offer_repo.decrement_quantity(offer_id, requested_qty, session=session)
        reservation = await reservation_repo.create(reservation_input, session=session)
        
        # Commit transaction (if any step failed, both operations rollback)
        await session.commit()
        
        return ReservationResult(success=True, reservation=reservation)
```

**Key Benefits of This Approach**:
- **Simple**: No background jobs, no TTL monitoring, no cleanup logic
- **Fast**: Lock held for ~200ms (vs 5 minutes in old payment-based approach)
- **Scalable**: Works across multiple bot instances via Redis
- **Safe**: Database transaction ensures no partial updates (inventory decremented but reservation fails)

**Error Handling**:
- **Lock Acquisition Failed**: "Another customer is reserving this offer right now. Please wait a moment and try again."
- **Insufficient Inventory**: "That was the last unit and someone just reserved it. Try another deal!"
- **Offer Expired During Reservation**: "This offer expired at [time]. Browse other deals with /browse"
- **Database Error**: "We couldn't complete your reservation. Please try again. Your inventory wasn't charged."

**Testing Strategy**:
1. **Unit Tests**: Mock Redis SETNX responses, test lock acquisition/release
2. **Integration Tests**: Test race condition with two concurrent reservation attempts
3. **Load Tests**: Verify performance under 100 simultaneous reservations
4. **Failure Tests**: Kill bot mid-transaction, verify database rollback works

**Redis Key Pattern**:
```
tmkt:lock:offer:<offer_id>  # TTL: 5 seconds
```

**No Per-Reservation Keys Needed** (unlike payment-based approach where we'd need):
```
# OLD (payment model, not needed now):
tmkt:reservation:<reservation_id>  # TTL: 300 seconds
tmkt:inventory:reserved:<offer_id>  # Counter for held units
```

---
        # Commit transaction (auto-commits on context exit)
        # Lock releases after commit
```

**Failure Recovery**:
- **Redis Down**: Lock acquisition fails → Return error to user: "Service temporarily unavailable"
- **Orphaned Locks**: TTL ensures automatic cleanup (max 5 minutes)
- **Deadlocks**: Cannot occur (only one lock per offer, FIFO acquisition)

**Monitoring**:
- Track lock acquisition failures (metric: `purchase_lock_conflict_count`)
- Monitor lock wait times (metric: `purchase_lock_wait_seconds`)
- Alert if lock acquisition failure rate > 5% (indicates high contention)

**Testing Strategy**:
1. **Unit Test**: Mock Redis `SETNX` response (success/failure)
2. **Integration Test**: Simulate concurrent purchases on same offer (use `asyncio.gather`)
3. **Stress Test**: 50 concurrent purchase attempts on offer with 1 item → Verify only 1 succeeds
4. **TTL Test**: Acquire lock, sleep 6 minutes, verify lock auto-released

**Performance**:
- **Lock Acquisition Time**: ~5-10ms (Redis network round-trip)
- **Lock Hold Time**: ~100-500ms (inventory check + DB write)
- **Throughput**: Can handle 1000+ concurrent lock requests (Redis ops are atomic)

**Gotchas**:
- Lock key naming: Use consistent prefix (`tmkt:lock:offer:{uuid}`) to avoid collisions
- Always use context manager pattern to ensure lock release (even on exceptions)
- Don't perform slow operations (API calls, file I/O) while holding lock
- Current `ttl_seconds=5` is incorrect; should be `300` for purchase flow

---

## 4. Image Storage for Photos

### Decision

**Use Azure Blob Storage with public blob access and SAS tokens** for serving business logos and offer photos.

Upload photos via Telegram Bot API (`getFile` → download → upload to Azure), store blob URLs in PostgreSQL.

### Rationale

1. **Microsoft Stack Alignment**: Project is in Microsoft ecosystem (Azure docs, Microsoft Learn integration), Azure Blob Storage is natural choice.

2. **SAS Token Security**: Generate time-limited, read-only SAS tokens for temporary public access vs permanently public blobs (better security).

3. **Python SDK Maturity**: `azure-storage-blob` SDK is well-documented, async-ready, and integrates with `DefaultAzureCredential`.

4. **Cost Efficiency**: Hot tier pricing ~$0.018/GB/month, minimal egress costs for small images (< 1MB each).

5. **CDN Integration**: Can enable Azure CDN later for global edge caching without code changes.

### Alternatives Considered

**AWS S3**
- **Pros**: 
  - Industry standard, extensive documentation
  - Slightly cheaper than Azure ($0.023/GB vs $0.018/GB)
  - Better global edge network (CloudFront)
- **Cons**:
  - Requires separate AWS account (additional vendor)
  - No alignment with project's Microsoft/Azure tooling
  - Similar feature parity as Azure Blob Storage
- **Why Not Chosen**: Azure Blob Storage is functionally equivalent and aligns with project ecosystem.

**Cloudflare R2**
- **Pros**: 
  - Zero egress fees (significant savings at scale)
  - S3-compatible API (easy migration from/to S3)
  - Fast global CDN by default
- **Cons**:
  - Newer service (less mature than S3/Azure)
  - Requires Cloudflare account setup
  - Less documentation for Python SDK
- **Why Not Chosen**: MVP doesn't need egress optimization yet; Azure is simpler choice.

**Self-Hosted Storage (MinIO on VM)**
- **Pros**: 
  - Full control over data
  - No per-GB storage costs (just VM cost)
  - S3-compatible API
- **Cons**:
  - Infrastructure management overhead (backups, scaling, monitoring)
  - Higher latency (single region vs multi-region CDN)
  - Security burden (SSL certificates, access control)
- **Why Not Chosen**: Managed service is better fit for MVP (focus on app logic, not ops).

**Database BLOBs (PostgreSQL `bytea`)**
- **Pros**: 
  - No additional infrastructure
  - Transactional consistency with metadata
- **Cons**:
  - Bloats database size (images don't compress well)
  - Slow queries (large BLOBs fragment across pages)
  - No CDN/edge caching
  - Database backups become huge
- **Why Not Chosen**: Anti-pattern to store large binaries in relational DB.

### Implementation Notes

**Upload Workflow** (business registration):
1. Business sends photo via Telegram → Bot receives `message.photo[-1]` (largest size)
2. Bot calls `context.bot.get_file(file_id)` → Gets temporary download URL
3. Bot downloads photo bytes → Uploads to Azure Blob Storage container `business-photos`
4. Azure returns blob URL (e.g., `https://account.blob.core.windows.net/business-photos/{business_id}.jpg`)
5. Bot stores URL in `businesses.photo_url` column
6. On offer listing, bot generates SAS token for read access (1 hour expiry)

**Azure Blob Storage Setup**:
```python
# src/storage/image_store.py (to be implemented)
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.identity import DefaultAzureCredential
from datetime import datetime, timedelta

class ImageStore:
    def __init__(self, account_url: str):
        self.account_url = account_url
        self.credential = DefaultAzureCredential()
        self.client = BlobServiceClient(account_url, credential=self.credential)
    
    async def upload_business_photo(self, business_id: UUID, photo_bytes: bytes) -> str:
        """Upload business logo to Azure Blob Storage."""
        container_name = "business-photos"
        blob_name = f"{business_id}.jpg"
        
        # Get container client (creates container if not exists)
        container_client = self.client.get_container_client(container_name)
        await container_client.create_container()  # Idempotent
        
        # Upload blob
        blob_client = container_client.get_blob_client(blob_name)
        await blob_client.upload_blob(photo_bytes, overwrite=True)
        
        return blob_client.url  # Returns permanent blob URL
    
    async def upload_offer_photo(self, offer_id: UUID, photo_bytes: bytes) -> str:
        """Upload offer photo to Azure Blob Storage."""
        container_name = "offer-photos"
        blob_name = f"{offer_id}.jpg"
        
        container_client = self.client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        await blob_client.upload_blob(photo_bytes, overwrite=True)
        
        return blob_client.url
    
    def generate_sas_url(self, blob_url: str, expiry_hours: int = 1) -> str:
        """Generate time-limited SAS token for public read access."""
        # Parse blob URL to extract account, container, blob name
        # (Simplified; real implementation needs URL parsing)
        container_name = "business-photos"  # Extract from blob_url
        blob_name = "some-uuid.jpg"  # Extract from blob_url
        
        sas_token = generate_blob_sas(
            account_name="account",
            container_name=container_name,
            blob_name=blob_name,
            account_key="...",  # From environment
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
        )
        
        return f"{blob_url}?{sas_token}"
```

**Telegram Photo Download**:
```python
# In business registration handler
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo_file = await update.message.photo[-1].get_file()  # Largest size
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Upload to Azure
    image_store: ImageStore = context.bot_data["image_store"]
    photo_url = await image_store.upload_business_photo(business_id, photo_bytes)
    
    # Store URL in database
    context.user_data["photo_url"] = photo_url
    return CONFIRMATION
```

**Access Control Options**:
1. **Public Blobs (No Auth)**: Set container to `PublicAccess.Blob` → URLs work without SAS token
   - **Pros**: Simple, no token generation overhead
   - **Cons**: Anyone with URL can access forever (security risk)
   - **Best For**: Public logos (low sensitivity)

2. **SAS Tokens (Time-Limited)**: Generate SAS token per request (1-hour expiry)
   - **Pros**: Temporary access, revocable (change account key)
   - **Cons**: Token generation adds latency (~10ms)
   - **Best For**: Offer photos (may want to revoke access)

3. **Private Blobs + Proxy**: Bot proxies blob data through own endpoint
   - **Pros**: Full control, can add watermarks/resize
   - **Cons**: Bot becomes bottleneck, high bandwidth usage
   - **Best For**: Not needed for MVP

**Recommendation**: Use **Public Blobs** for business logos (permanent, low-risk) and **SAS Tokens** for offer photos (temporary, can revoke).

**Configuration** (`.env`):
```bash
AZURE_STORAGE_ACCOUNT_URL=https://toogoodtogo.blob.core.windows.net
AZURE_STORAGE_ACCOUNT_KEY=...  # For SAS token generation
```

**Image Processing**:
```python
# Optional: Resize/compress before upload to save storage/bandwidth
from PIL import Image
import io

def resize_image(photo_bytes: bytes, max_width: int = 800) -> bytes:
    """Resize image to max width while preserving aspect ratio."""
    img = Image.open(io.BytesIO(photo_bytes))
    
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()
```

**Error Handling**:
- **Upload Failure**: Retry 3 times with exponential backoff → Fallback: Allow registration without photo (photo_url = NULL)
- **Invalid Image Format**: Validate `message.photo` exists before download → Show error: "Please send a valid photo"
- **Size Limits**: Telegram max photo size is 10MB (enforced by API), resize to 1MB before upload

**Testing Strategy**:
1. **Unit Test**: Mock `BlobServiceClient.upload_blob()` response
2. **Integration Test**: Upload test image to Azure dev container, verify URL accessibility
3. **E2E Test**: Send photo via Telegram test bot, verify blob uploaded and URL stored in DB

**Cost Estimation** (MVP):
- Storage: 1000 businesses × 500KB logo + 5000 offers × 500KB photo = ~2.75 GB → $0.05/month
- Transactions: 10K uploads + 100K reads/month → $0.01/month
- **Total**: < $0.10/month (negligible)

**Gotchas**:
- Telegram photo `file_id` is temporary (expires after download); don't store it
- `message.photo` is array of multiple sizes (thumbnail to full); use `[-1]` for largest
- Azure container names must be lowercase (enforce in code)
- SAS token expiry should exceed expected page view time (1 hour is safe)

---

## 5. Background Job Scheduling (1-Minute Expiration Checks)

### Decision

**Use asyncio task with 60-second sleep loop** running alongside bot event loop in same process.

Implement `SchedulerService` with `start()` method that spawns background task for periodic offer expiration checks.

### Rationale

1. **Simplicity**: Single-process deployment, no separate worker process or message queue required.

2. **Tight Integration**: Scheduler accesses same database connection pool and services as bot handlers.

3. **Lightweight**: No external scheduler infrastructure (Celery broker, Redis queue, cron daemon).

4. **Async-Native**: Runs concurrently with bot event loop without blocking user requests.

5. **Already Implemented**: Codebase has `SchedulerService` (`src/services/scheduler.py`) with this pattern.

### Alternatives Considered

**APScheduler (Async Job Scheduler)**
- **Pros**: 
  - Feature-rich (cron expressions, interval/date triggers, job persistence)
  - Built-in error handling and retry logic
  - Thread/process executors for blocking tasks
- **Cons**:
  - Additional dependency (10+ packages)
  - Overkill for single periodic task (1-minute interval)
  - Adds complexity (job stores, executor pools)
- **Why Not Chosen**: Simple asyncio loop is sufficient for MVP; APScheduler is over-engineered.

**Celery (Distributed Task Queue)**
- **Pros**: 
  - Industry standard for async jobs
  - Supports multiple workers, task prioritization
  - Built-in monitoring (Flower), retries, rate limiting
- **Cons**:
  - Requires message broker (Redis/RabbitMQ) for task queue
  - Separate worker process (increases deployment complexity)
  - Heavy for single 1-minute job (MB of dependencies)
- **Why Not Chosen**: MVP doesn't need distributed workers or complex task routing. Overkill.

**Cron Jobs (System-Level Scheduler)**
- **Pros**: 
  - OS-native, no code dependencies
  - Reliable (systemd/cron daemon restarts on crash)
- **Cons**:
  - Requires separate Python script (can't share bot's DB connections)
  - Platform-specific (crontab on Linux, Task Scheduler on Windows)
  - No asyncio integration (synchronous execution)
- **Why Not Chosen**: Deployment complexity (manage separate scheduled job) and can't reuse bot infrastructure.

**Database Triggers (PostgreSQL)**
- **Pros**: 
  - Runs in database (no application code)
  - Guaranteed execution (ACID transactions)
- **Cons**:
  - PL/pgSQL triggers don't support time-based execution (need polling table)
  - Can't send Telegram messages (no bot integration)
  - Complex debugging
- **Why Not Chosen**: DB triggers aren't designed for scheduled background jobs.

### Implementation Notes

**Current Implementation** (`src/services/scheduler.py`):
```python
class SchedulerService:
    def __init__(self, offer_repo: PostgresOfferRepository, interval_seconds: int = 60):
        self.offer_repo = offer_repo
        self.interval_seconds = interval_seconds
        self._running = False

    async def start(self) -> None:
        """Start scheduler loop."""
        self._running = True
        logger.info("Scheduler started", interval_seconds=self.interval_seconds)

        while self._running:
            try:
                await self.expire_offers()
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                logger.error("Scheduler error", error=str(e))
                await asyncio.sleep(self.interval_seconds)  # Continue on error

    async def stop(self) -> None:
        """Stop scheduler loop."""
        self._running = False
        logger.info("Scheduler stopped")

    async def expire_offers(self) -> None:
        """Mark expired offers as EXPIRED."""
        expired = await self.offer_repo.get_expired_offers()
        for offer in expired:
            await self.offer_repo.update_status(offer.id, OfferStatus.EXPIRED)
            logger.info("Offer expired", offer_id=str(offer.id))
```

**Integration with Bot** (`src/bot/run.py`):
```python
async def main():
    # Initialize bot
    app = Application.builder().token(settings.bot_token).build()
    
    # Initialize database and repositories
    db = get_database()
    await db.connect()
    
    async with db.session() as session:
        offer_repo = PostgresOfferRepository(session)
        
        # Start scheduler as background task
        scheduler = SchedulerService(offer_repo, interval_seconds=60)
        scheduler_task = asyncio.create_task(scheduler.start())
        
        # Start bot
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        # Keep running until interrupted
        try:
            await asyncio.Event().wait()  # Block forever
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            await scheduler.stop()
            scheduler_task.cancel()
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            await db.disconnect()
```

**Query for Expired Offers** (`src/storage/postgres_offer_repo.py`):
```python
async def get_expired_offers(self) -> list[Offer]:
    """Get offers past end_time with active status."""
    stmt = (
        select(OfferTable)
        .where(OfferTable.status == OfferStatus.ACTIVE)
        .where(OfferTable.end_time <= datetime.utcnow())
    )
    result = await self.session.execute(stmt)
    return [self._to_domain_model(db_offer) for db_offer in result.scalars().all()]
```

**Expiration Logic**:
1. Every 60 seconds, query database for offers where:
   - `status = 'ACTIVE'`
   - `end_time <= now()`
2. For each expired offer:
   - Update `status` to `'EXPIRED'`
   - Log event: `offer_expired(offer_id, business_id, end_time)`
3. Sleep 60 seconds, repeat

**Error Handling**:
- **Database Connection Lost**: Catch exception in loop → Log error → Continue (retry next iteration)
- **Transaction Deadlock**: Retry update 3 times with exponential backoff
- **Scheduler Crash**: Bot process exits → Scheduler stops (restarts with bot)

**Graceful Shutdown**:
```python
# Stop scheduler on bot shutdown
await scheduler.stop()  # Sets _running = False
await asyncio.wait_for(scheduler_task, timeout=5.0)  # Wait for current iteration to finish
```

**Monitoring**:
- Log each expiration check: `scheduler_check(expired_count, duration_ms)`
- Track expired offers per check (metric: `offers_expired_per_check`)
- Alert if scheduler stops running (heartbeat check)

**Performance Considerations**:
- **Query Time**: ~10-50ms for 1000 active offers (indexed on `status` + `end_time`)
- **Update Time**: ~5ms per offer × N expired offers (typically < 10 per minute)
- **Total Overhead**: < 100ms per minute (negligible vs bot response time)

**Scalability**:
- **Single Instance**: Works up to ~10K active offers (query time < 500ms)
- **Multiple Instances**: Requires distributed lock to prevent duplicate expiration (Redis lock: `tmkt:lock:scheduler`)
- **High Volume**: Migrate to dedicated worker process with Celery

**Testing Strategy**:
1. **Unit Test**: Mock `offer_repo.get_expired_offers()` to return test offers → Verify `update_status` called
2. **Integration Test**: Create offer with `end_time` in past → Run `expire_offers()` once → Verify status changed
3. **E2E Test**: Create offer expiring in 10 seconds → Run scheduler → Wait 20 seconds → Verify offer expired
4. **Stress Test**: Create 1000 offers all expiring at same time → Verify scheduler handles batch expiration

**Timing Accuracy**:
- **Interval**: 60 seconds ± processing time (~100ms) = ~60.1 seconds actual
- **Expiration Lag**: Offers expire up to 60 seconds after `end_time` (acceptable for MVP)
- **Improvement**: Use `while (next_run := now() + 60): await asyncio.sleep(next_run - now())` to maintain exact 60s intervals

**Alternative: Immediate Expiration Check**:
```python
# In offer creation handler
async def create_offer(...):
    offer = await offer_repo.create(offer_input)
    
    # Schedule immediate expiration check at end_time
    delay_seconds = (offer.end_time - datetime.utcnow()).total_seconds()
    asyncio.create_task(expire_offer_after_delay(offer.id, delay_seconds))
```
**Pros**: Instant expiration at exact `end_time`  
**Cons**: One task per offer (memory overhead for 1000s of offers)  
**Not Chosen**: Polling every 60 seconds is simpler and more scalable.

**Gotchas**:
- Use `await asyncio.sleep()` not `time.sleep()` (blocks event loop)
- Handle `CancelledError` in scheduler task (graceful shutdown)
- Don't run heavy DB queries in scheduler (use `LIMIT` if batch processing)
- Index `offers(status, end_time)` for fast expiration queries (already exists in schema)

---

## Summary

| Area | Decision | Key Rationale |
|------|----------|---------------|
| **Payment Model** | On-Site Payment (Immediate Reservation) | Simpler MVP, no payment provider complexity, business flexibility, 70% less code than Stripe integration |
| **Geolocation** | Haversine + App-Level Filtering | Sufficient for MVP (<1000 offers), no PostGIS dependency, can migrate later |
| **Reservation Locks** | Redis SETNX + 5-second TTL | Atomic, auto-expiry, transactional lock only (not long-duration hold) - **current implementation is correct** |
| **Image Storage** | Azure Blob Storage + SAS | Microsoft stack alignment, cost-efficient, CDN-ready |
| **Scheduler** | Asyncio Loop + 60s Sleep | Lightweight, async-native, no external dependencies |

All decisions prioritize **MVP simplicity** while maintaining **migration paths** to more sophisticated solutions (online payments, PostGIS, Celery, CDN) if usage scales beyond current assumptions.

**Key Architectural Changes from Original Plan**:
- ❌ **Removed**: Stripe integration, webhook handling, payment flow logic, refund processing
- ✅ **Simplified**: Immediate inventory decrement on reservation (no temporary holds), no background job for reservation cleanup
- ✅ **Preserved**: Redis locking for race condition prevention (5-second TTL is correct for transactional locks)

**Next Steps**:
1. Rename `Purchase` entity → `Reservation` in data model and database
2. Remove `stripe_checkout.py` service and webhook handlers
3. Update handler contracts to show "Reserve" button instead of "Pay"
4. Implement Haversine distance calculation in `DiscoveryRankingService`
5. Add `ImageStore` class for Azure Blob upload/SAS generation
6. Verify scheduler integration in `bot/run.py` startup sequence
7. Add integration tests for reservation race conditions


