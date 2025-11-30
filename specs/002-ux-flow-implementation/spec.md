# Feature Specification: Telegram Marketplace Bot UX Flow Implementation

**Feature Branch**: `002-ux-flow-implementation`  
**Created**: 2025-11-30  
**Status**: Draft  
**Input**: User description: "Implement comprehensive UX flow for Telegram marketplace bot with native features including commands, keyboards, inline buttons, payments, and offer lifecycle management"

## Clarifications

### Session 2025-11-30 (Initial)

- Q: When a customer initiates reservation (FR-015), how should inventory be managed? → A: Reservation immediately decrements inventory (no temporary hold with auto-release)
- Q: What distance qualifies as "nearby" for the customer browse Nearby filter (FR-010)? → A: 5km (3 miles) radius
- Q: How frequently should the system check for expired offers (FR-004)? → A: 1 minute intervals
- Q: What events should be logged for operational monitoring, debugging, and business analytics? → A: Key business events - Offer lifecycle, reservations, cancellations, errors with structured data

### Session 2025-11-30 (Payment Model Update)

- **Payment approach**: On-site payment model selected. Customers reserve items through the bot and pay at pickup (cash, card, or business's preferred method). This simplifies MVP implementation by removing payment provider integration complexity while still enabling the core marketplace value proposition.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Business Posts a Deal (Priority: P1)

A registered, verified business wants to post an excess-produce deal quickly through the Telegram bot so customers can discover and purchase it before closing time.

**Why this priority**: This is the core value proposition - enabling businesses to monetize excess inventory. Without this, there is no marketplace content for customers.

**Independent Test**: A verified business can complete the full deal posting flow (from `/newdeal` command to published offer visible to customers) and see confirmation that their offer is live. This delivers value by allowing businesses to list inventory immediately.

**Acceptance Scenarios**:

1. **Given** a verified business is registered, **When** they trigger `/newdeal` and provide all required fields (title, description, photo, time window, quantity, price), **Then** the system publishes the offer as ACTIVE and confirms with a message showing the deal details and a share link.

2. **Given** a business is filling out a new deal, **When** they provide an invalid value (e.g., negative quantity or price), **Then** the system shows a clear error message with an example of correct format and allows them to retry.

3. **Given** a business completes deal creation, **When** the offer is published, **Then** customers searching nearby deals can immediately see this offer in their browse results.

4. **Given** a business has posted a deal with end time of 21:00, **When** the current time reaches 21:00, **Then** the system automatically marks the offer as EXPIRED and removes it from customer browse results.

---

### User Story 2 - Customer Discovers and Reserves a Deal (Priority: P1)

A customer wants to quickly browse nearby deals, see clear details including remaining quantity and pickup time, and reserve items for on-site payment at pickup.

**Why this priority**: This is the demand side of the marketplace - without customer reservations, businesses gain no value from posting deals. The reservation flow must be frictionless to drive conversion while keeping payment simple (on-site).

**Independent Test**: A customer can use `/browse` to see active offers, select one, specify quantity, confirm reservation, and receive a confirmation with order ID and pickup instructions indicating payment will be made on-site. This delivers immediate value by enabling food rescue reservations.

**Acceptance Scenarios**:

1. **Given** active offers exist nearby, **When** a customer uses `/browse`, **Then** they see a paginated list of offer cards showing key details (business name, address, price, pickup time, units left) with inline buttons for navigation.

2. **Given** a customer views offer details, **When** they tap the Reserve button and select quantity, **Then** the system reserves those units and shows confirmation prompt "Reserve [X] items for [Total Price]? Payment on-site at pickup."

3. **Given** a customer confirms reservation, **When** confirmation is processed, **Then** the system creates the reservation, decrements inventory, sends a confirmation message with order ID, pickup address, time window, total amount to pay, and instructions: "Pay [amount] on-site when you pick up."

4. **Given** a customer attempts to reserve the last unit, **When** another customer completes reservation of that unit first (race condition), **Then** the first customer sees an error message "That was the last unit and someone just reserved it" and the Reserve button is disabled.

5. **Given** an offer has expired or been paused, **When** a customer attempts to reserve from an old message, **Then** the system shows a clear error explaining the offer is no longer available.

6. **Given** a customer has completed reservation, **When** they use `/my_reservations`, **Then** they see a list of their active reservations with pickup details, amount to pay, and status.

---

### User Story 3 - Business Manages Offer Lifecycle (Priority: P2)

A business wants to pause, edit, or end their active offers based on changing inventory or circumstances, and customers should always see accurate real-time status.

**Why this priority**: Operational flexibility is essential for businesses to manage unexpected changes (early sellout, need to pause temporarily, price adjustments). This prevents customer disappointment and builds trust.

**Independent Test**: A business can access `/myoffers`, select an active offer, pause it (making it invisible to customers with Buy buttons disabled), edit quantity or price, or end it early. Changes are immediately reflected in customer views.

**Acceptance Scenarios**:

1. **Given** a business has active offers, **When** they use `/myoffers`, **Then** they see a list of their offers with status (Active/Paused) and inline management buttons (Pause/Resume, Edit, End now).

2. **Given** a business pauses an offer, **When** customers view that offer, **Then** they see a "Paused" indicator and the Buy button is disabled with explanation that the business temporarily paused the offer.

3. **Given** a business edits quantity to 0, **When** the update is saved, **Then** the offer state changes to SOLD_OUT and customers see "Sold out" with Buy button disabled.

4. **Given** a business edits the price, **When** the update is saved, **Then** all customer-facing offer cards immediately reflect the new price.

5. **Given** a business taps "End now" and confirms, **When** the offer is ended, **Then** the state changes to EXPIRED_EARLY and customers see "Expired" with no Buy option.

---

### User Story 4 - Business Onboarding and Registration (Priority: P1)

A new business user wants to register their business through the Telegram bot with minimal friction, provide required details (name, address, contact), and get approved so they can start posting deals.

**Why this priority**: Without a smooth onboarding process, businesses cannot enter the marketplace. This is the entry point for supply-side growth.

**Independent Test**: A new user can start the bot, select "I'm a business", complete the registration form (name, address, photo), submit for approval, and receive notification when approved. Upon approval, they can immediately post deals.

**Acceptance Scenarios**:

1. **Given** a new user starts the bot, **When** they select "I'm a business", **Then** they are guided through a step-by-step registration flow collecting business name, address (street, city, postal code), optional phone, and logo/photo.

2. **Given** a business completes registration, **When** they submit for approval, **Then** they receive a confirmation message explaining admin approval is required and they'll be notified via the bot.

3. **Given** an admin approves the business, **When** approval is complete, **Then** the bot sends a notification to the business with a "Post a deal now" button.

4. **Given** a business provides incomplete address information, **When** they attempt to continue, **Then** the system shows which required field is missing with a clear example.

---

### User Story 5 - Customer Cancels Reservation Before Pickup (Priority: P3)

A customer who has reserved a deal wants to cancel it before the pickup window ends, allowing the units to return to available inventory for others.

**Why this priority**: While cancellations should be rare, supporting them improves customer trust and allows inventory to return to available pool if plans change. Since no payment has occurred yet, cancellation is straightforward.

**Independent Test**: A customer with an active reservation can access `/my_reservations`, select a reservation that hasn't reached pickup end time yet, tap Cancel, confirm the action, and see the reservation marked as cancelled with units returned to inventory.

**Acceptance Scenarios**:

1. **Given** a customer has an active reservation before pickup end time, **When** they view it in `/my_reservations` and tap Cancel, **Then** they see a confirmation prompt "Cancel this reservation? The items will become available for others."

2. **Given** a customer confirms cancellation, **When** cancellation is processed, **Then** the reservation is marked CANCELLED, the reserved units are returned to offer inventory, and customer sees confirmation.

3. **Given** a customer attempts to cancel after pickup end time, **When** they view the reservation, **Then** no Cancel button is shown.

---

### Edge Cases

- **Offer expires during reservation**: If a customer is viewing an offer detail page when the offer end time passes, the system validates expiration before processing reservation and shows error: "This offer expired at [time]."

- **Business deletes or pauses offer during customer reservation**: If offer state changes to PAUSED or UNPUBLISHED while reservation is in progress, the system rejects the reservation and shows: "This offer is currently unavailable. Try another deal."

- **Zero inventory during reservation attempt**: If available quantity reaches 0 due to another transaction, the system immediately shows "Sold out" and disables Reserve buttons across all customer views.

- **Invalid or ambiguous business address**: If business registration includes incomplete address (missing city or postal code), the system prompts: "I couldn't find the [field] field. Please send [example]." On customer side, if address is malformed, show: "Address unavailable - please contact the venue."

- **Duplicate registrations**: If a business attempts to register multiple times, system checks for existing business by name + address combination and prompts: "A business with this name and address already exists. Contact support if you need access."

- **Rapid quantity changes**: If business rapidly edits quantity up and down during active reservations, system maintains transactional integrity through reservation locks and ensures no overselling occurs.

- **Customer no-show**: If a customer reserves but doesn't show up during pickup window, the reservation automatically expires at pickup end time and units remain decremented (business handles no-shows manually).

## Requirements *(mandatory)*

### Functional Requirements

#### Business Features

- **FR-001**: System MUST allow verified businesses to create offers with mandatory fields: title, description, photo (optional but recommended), time window (pickup start and end), quantity (integer > 0), and price (decimal > 0).

- **FR-002**: System MUST validate all offer fields before publishing and provide clear error messages with examples for invalid inputs (e.g., "That doesn't look like a number. Send just the amount, e.g. `5` or `4.50`").

- **FR-003**: System MUST require business registration (name, address, optional contact, optional photo) and manual admin approval before allowing businesses to post offers.

- **FR-004**: System MUST automatically expire offers when current time exceeds the offer end time, changing state to EXPIRED and removing from customer browse results, with expiration checks running every 1 minute.

- **FR-005**: Businesses MUST be able to pause active offers, which sets state to PAUSED, adds a paused indicator to customer views, and disables Buy buttons.

- **FR-006**: Businesses MUST be able to edit offer fields (price, quantity, time window, description) on active or paused offers, with changes reflected immediately in all customer views.

- **FR-007**: Businesses MUST be able to end offers early, which sets state to EXPIRED_EARLY and removes from customer browse results.

- **FR-008**: System MUST provide businesses with `/myoffers` command showing all their offers with status and management buttons (Pause/Resume, Edit, End now, View as customer).

- **FR-009**: System MUST generate shareable deep links for each published offer in format `https://t.me/bot_name?start=offer_<offer_id>`.

#### Customer Features

- **FR-010**: System MUST provide customers with `/browse` command to discover active offers, with optional filters (Nearby within 5km/3 miles radius, All deals, Ending soon).

- **FR-011**: System MUST display offer cards showing business name, address (short form), price, pickup time window, and remaining units.

- **FR-012**: Customers MUST be able to view detailed offer information including full address, complete description, and photo.

- **FR-013**: System MUST provide quantity selector (with +/- buttons) limited by available inventory when customer views offer details.

- **FR-014**: System MUST implement reservation confirmation flow showing total price and payment instructions ("Payment on-site at pickup") before creating reservation.

- **FR-015**: System MUST create confirmed reservation and immediately decrement inventory when customer confirms reservation, with no automatic release (cancellation must be manual via `/my_reservations`).

- **FR-016**: System MUST prevent overselling by enforcing atomic inventory reservation and showing error "That was the last unit and someone just reserved it" when race conditions occur.

- **FR-017**: System MUST send reservation confirmation message with order ID, business name and address, pickup time window, total amount to pay on-site, and pickup instructions.

- **FR-018**: Customers MUST be able to view their reservations via `/my_reservations` command showing order ID, pickup details, amount to pay, and status.

- **FR-019**: Customers MUST be able to cancel reservations before pickup end time, which marks reservation as CANCELLED and returns units to inventory.

#### Navigation and Commands

- **FR-020**: System MUST implement command scopes so businesses see business-specific commands (`/register_business`, `/newdeal`, `/myoffers`) and customers see customer-specific commands (`/browse`, `/my_reservations`).

- **FR-021**: System MUST provide global commands accessible to all users: `/start` (entry point with role selection), `/help` (feature explanations), `/settings` (language and notification preferences).

- **FR-022**: System MUST support deep linking via `/start` command with parameters for business invites (`business_invite_<token>`) and direct offer views (`offer_<offer_id>`).

- **FR-023**: System MUST implement reply keyboards for simple selections (role selection, filters) marked as `one_time_keyboard=true` to hide after use.

- **FR-024**: System MUST implement inline keyboards for interactive actions (Reserve buttons, pagination, management actions) that update existing messages rather than sending new ones.

- **FR-025**: System MUST configure menu button to show role-appropriate commands (businesses see "New deal", "My offers", "Help"; customers see "Browse deals", "My reservations", "Help").

#### Error Handling and States

- **FR-026**: System MUST validate offer availability before processing reservation and reject with clear message if offer is expired, paused, or sold out.

- **FR-027**: System MUST track offer states: ACTIVE, PAUSED, EXPIRED, EXPIRED_EARLY, SOLD_OUT and enforce appropriate visibility and action permissions for each state.

- **FR-028**: System MUST provide clear, actionable error messages following pattern: [emoji status indicator] [what went wrong] [what to do next or example].

- **FR-029**: System MUST log key business events with structured data including: offer state transitions (created, published, paused, expired, sold out), reservation lifecycle (reservation created, reservation confirmed, reservation cancelled), inventory changes, and all application errors with contextual metadata for debugging and analytics.

### Key Entities

- **Business**: Represents a registered venue or shop. Attributes include business name, address (street, city, postal code), optional contact phone, optional logo/photo, verification status (pending/approved), and registration timestamp.

- **Offer**: Represents a deal posted by a business. Attributes include title, description, optional photo, price per unit, quantity (total and remaining), pickup time window (start and end), offer state (ACTIVE/PAUSED/EXPIRED/SOLD_OUT/EXPIRED_EARLY), category (optional), creation timestamp, and relationship to Business.

- **Reservation**: Represents a customer's confirmed reservation for on-site payment. Attributes include order ID, quantity reserved, total price (to be paid on-site), reservation timestamp, pickup time window (inherited from Offer), reservation status (CONFIRMED/CANCELLED), and relationships to Customer and Offer.

- **User**: Represents any bot user. Attributes include Telegram user ID, role (BUSINESS/CUSTOMER), language preference, notification settings, and registration timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Verified businesses can create and publish a complete offer in under 2 minutes from initiating `/newdeal` to receiving confirmation message.

- **SC-002**: 95% of reservation attempts complete successfully without errors (excluding user-initiated cancellations or sold-out items).

- **SC-003**: Customers can see a relevant active deal within 10 seconds of using `/browse` command.

- **SC-004**: Overselling occurs in less than 0.1% of transactions when multiple customers attempt to reserve the last unit simultaneously.

- **SC-005**: Reservation confirmation messages include all required information (order ID, business address, pickup time, amount to pay on-site, pickup instructions) in 100% of successful reservations.

- **SC-006**: Businesses can pause, edit, or end an offer within 5 seconds, with changes reflected in customer views within 2 seconds.

- **SC-007**: Error messages are clear and actionable in 100% of error scenarios, following the pattern: status indicator + problem description + suggested action.

- **SC-008**: New businesses can complete registration in under 3 minutes from starting the bot to submitting for approval.

- **SC-009**: Customers can complete reservation cancellation (if before pickup time) in under 30 seconds from opening `/my_reservations` to receiving cancellation confirmation.

- **SC-010**: 90% of customers successfully complete their first reservation attempt without needing to retry or seek help.

## Assumptions *(optional)*

- Telegram bot API maintains 99.9% uptime during marketplace operating hours.

- Businesses handle on-site payments manually (cash, card terminal, or other methods at their discretion).

- Admin business verification occurs within 24 hours of registration submission on average.

- Businesses operate in a single geographic market initially (single currency, single language).

- Pickup time windows are same-day or next-day only (no multi-day advance bookings).

- Mobile network connectivity for users is sufficient for photo uploads (typically 1-5 MB per image).

- Users have Telegram installed and are familiar with basic bot interactions (sending commands, tapping buttons).

## Scope Boundaries *(optional)*

### In Scope

- Complete UX flows for business onboarding, offer posting, and offer management
- Complete UX flows for customer discovery, reservation, and reservation management  
- Integration with Telegram's native UI elements (commands, keyboards, inline buttons)
- On-site payment model (customers pay at pickup, not through app)
- Real-time inventory management and reservation system
- Admin approval workflow for new businesses
- Deep linking for offer sharing and contextual entry
- Error handling for common edge cases (race conditions, expiration, pauses)

### Out of Scope

- Web-based admin dashboard (admin approval handled via separate internal tool initially)
- Multi-language support (English only for MVP, infrastructure prepared for future expansion)
- Advanced search and filtering (beyond Nearby/All/Ending soon)
- Customer ratings and reviews of businesses or offers
- Business analytics dashboard (metrics tracked server-side but no user-facing display)
- Automated fraud detection or business verification (manual admin approval only)
- In-app messaging between customers and businesses (contact via phone if needed)
- QR code generation for redemption (order ID display only)
- Payment processing through app (customers pay on-site only)
- Refund processing (no refunds since payment is on-site)
- Subscription or membership features for businesses or customers
- Payment tracking or receipt generation (businesses handle their own payment records)

## Dependencies *(optional)*

- **Telegram Bot API**: Core platform for all user interactions, requires bot token from BotFather
- **Geolocation services**: For "Nearby" filtering, requires geocoding API (e.g., Google Maps, Mapbox)
- **Image storage**: For business logos and offer photos, requires cloud storage (e.g., AWS S3, Cloudflare R2)
- **Admin approval mechanism**: External or internal tool for business verification, requires integration endpoint

## Open Questions *(optional)*

None at this time. All critical decisions have been made based on the comprehensive UX flow design document.
