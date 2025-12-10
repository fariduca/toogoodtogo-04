# UX Flow Design for Telegram Marketplace Bot  
**Use case:** Marketplace for restaurants & shops to post excess-produce deals; customers browse and buy via a Telegram Bot. :contentReference[oaicite:0]{index=0}  

---

## 1. Design Goals

We’ll use Telegram’s native bot features (commands, reply keyboards, inline keyboards, menu button, deep links, payments) to build a marketplace that is:

- **Usable** – clear next step on every screen, minimal typing.
- **Accessible** – simple language, high contrast button labels, keyboard-only operation (no “tiny tap targets”).
- **Consistent** – same patterns for all flows (`/start`, “Back”, “Cancel”, confirmation screens).
- **Efficient** – 2 minutes or less for a business to post a deal (SC-001); 10 seconds to see a nearby deal (SC-003).
- **Feedback-rich** – visible loading, success, and error states.
- **Visually clear** – concise messages + structured lists + focused inline keyboards.
- **Emotionally engaging** – friendly tone, “you’re saving food & money” messaging.
- **User-centred** – flows separately optimised for **businesses** and **customers**, mapped to the three user stories.

Telegram gives us:  

- **Commands**, **keyboards** and **buttons** to build flexible interfaces with minimal typing. :contentReference[oaicite:1]{index=1}  
- **Custom reply keyboards** that temporarily replace the user’s keyboard with predefined options. :contentReference[oaicite:2]{index=2}  
- **Inline keyboards** with callback / URL / payment buttons that work behind the scenes. :contentReference[oaicite:3]{index=3}  
- **Menu button & global commands** (`/start`, `/help`, `/settings`) for a consistent entry point. :contentReference[oaicite:4]{index=4}  
- **Deep links** (`https://t.me/your_bot?start=...`) to start contextual flows. :contentReference[oaicite:5]{index=5}  
- **Payments** via invoices and a pay button, with third-party providers like Stripe behind the scenes. :contentReference[oaicite:6]{index=6}  

---

## 2. Telegram Features We’ll Use (Input & Interaction Layer)

### 2.1 Commands

- `/start` – entry point for both business and customer; can receive deep-link parameters for context.
- `/help` – show how to post deals, browse, pay, and redeem.
- `/settings` – language, notification preferences.
- Business-only:
  - `/register_business`
  - `/newdeal`
  - `/myoffers`
- Customer-only:
  - `/browse`
  - `/my_purchases`

**Why commands?**  
Telegram highlights commands, auto-completes them, and exposes them via the menu button, reducing typing and making the bot more discoverable. :contentReference[oaicite:7]{index=7}  

We’ll configure command scopes so businesses and customers see different command sets.

---

### 2.2 Custom Reply Keyboards

Used where the user should pick from a **short, simple set** of options instead of typing:

- “I am a…” → `Business` / `Customer`
- Business registration steps (e.g. country, city list).
- Simple filters for customers (e.g. “Nearby”, “All deals”, “Ending soon”).

Telegram shows reply keyboards instead of the system keyboard; tapping an option sends its text as a message instantly. :contentReference[oaicite:8]{index=8}  

We’ll usually mark them `one_time_keyboard = true` so the keyboard hides after selection, keeping the chat clean. :contentReference[oaicite:9]{index=9}  

---

### 2.3 Inline Keyboards (Callback / URL / Payment Buttons)

Inline keyboards sit **under a specific message** and don’t send visible chat messages when tapped; instead they produce callback data we can handle invisibly. :contentReference[oaicite:10]{index=10}  

We’ll use them for:

- Business deal summary:  
  - `[Publish]`, `[Edit]`, `[Cancel]`
- Offer cards for customers:
  - `[View items]`, `[Buy]`, `[Share]`, `[Next]`, `[Prev]`
- Offer management:
  - `[Pause]`, `[Resume]`, `[End now]`, `[Edit quantity]`
- Payment / checkout:
  - **Option A (native Telegram payment)** – invoice with `Pay` button.
  - **Option B (external Stripe Checkout)** – URL button to hosted checkout page.

Using callback buttons lets us update the inline keyboard instead of sending new messages (e.g. toggling “Paused” → “Active”), which Telegram explicitly recommends for smoother UX. :contentReference[oaicite:11]{index=11}  

---

### 2.4 Menu Button & Global Commands

Telegram’s menu button can show a short list of bot commands or open a Web App. :contentReference[oaicite:12]{index=12}  

For this bot:

- **Business profile menu:**
  - `New deal`
  - `My offers`
  - `Help`
- **Customer profile menu:**
  - `Browse deals`
  - `My purchases`
  - `Help`

Global commands:

- `/start` – start / restart the flow.
- `/help` – short explanation + quick buttons to “Post a deal” / “Browse deals”.
- `/settings` – language & notification toggles.

This ensures consistent navigation even if the user “gets lost”.

---

### 2.5 Deep Linking

For contextual entry into the bot:

- `https://t.me/marketplace_bot?start=business_invite_<token>`  
  → Open `/start` pre-filled with a token that maps to a pending business application.
- `https://t.me/marketplace_bot?start=offer_<offer_id>`  
  → Open the detailed view of a specific offer for direct promotion.

Telegram supports such `start` parameters and delivers them as `/start <parameter>` to the bot. :contentReference[oaicite:13]{index=13}  

---

### 2.6 Payments

The spec requires external payment processing (e.g. Stripe Checkout). We can satisfy this in **two compatible ways**:

1. **Native Telegram Payments with Stripe provider**

   - Use `sendInvoice` to create an invoice for the selected offer and quantity.
   - Telegram shows a **Pay** button and a secure payment sheet.
   - Telegram sends sensitive card data directly to Stripe and other providers, not to your bot. :contentReference[oaicite:14]{index=14}  
   - Flow:
     - Send invoice.
     - Receive `pre_checkout_query`.
     - Validate inventory & accept via `answerPreCheckoutQuery`.
     - Receive `successful_payment` service message and update purchase record. :contentReference[oaicite:15]{index=15}  

2. **External hosted checkout page via URL button**

   - Inline keyboard button `[Pay with card]` opens `https://checkout.stripe.com/...` (or similar).
   - Telegram warns the user before opening external link; good for transparency. :contentReference[oaicite:16]{index=16}  

You can implement **Option 1 now**, and still use Stripe behind the scenes (satisfies FR-011), while keeping friction low.

---

## 3. UX Flow for User Story 1 – Business Posts a Deal (P1)

**Goal:** Allow a registered, verified business to publish an offer in under 2 minutes (SC-001) with all required fields (FR-001, FR-002, FR-004).

### 3.1 Onboarding & Role Selection

**Entry points**

- Deep link from email / web:  
  `https://t.me/marketplace_bot?start=business_invite_<token>`
- Manual search for `@marketplace_bot` and tapping **Start**.

**Flow**

1. **System → Business (message, no keyboard)**  
   > “Hi 👋 I help you sell today’s excess produce at a discount.  
   > What describes you best?”

   Reply keyboard: `[I’m a business]` `[I’m a customer]`

2. **Business taps `I’m a business`**  
   - Bot:
     > “Great! Let’s register your business. It takes ~1 minute.”

   Inline keyboard: `[Register business]` `[Help]`  

3. **On `/register_business` or button tap**

   - Collect:
     - Business name (free text).
     - Venue address (structured):
       - Street line
       - City
       - Postal code
       - Optional: map link or coordinates
     - Contact phone (optional but recommended).
     - Logo or venue photo (prompt to send photo).
   - At each step:
     - Provide **clear example**:
       > “Street & number (e.g. ‘Main St 21B’)”

   - Validation:
     - If missing required field (address, city, postal code), respond:
       > “I couldn’t find the **city** field.  
       > Please send your city name (e.g. ‘Helsinki’).”

   - When all fields valid:
     - Summary message (with photo preview) + inline keyboard:  
       `[Confirm & submit for approval]` `[Edit]` `[Cancel]`

4. **Manual admin approval (FR-012)**

   - State in UI:
     > “Thanks! An admin will verify your business (name + address only).  
     > You’ll get a notification here when you’re approved.”

   - When approved:
     - Bot sends:
       > “✅ Your business is approved.  
       > You can now post deals that customers see instantly.”

     Inline keyboard: `[Post a deal now]` `[Learn how it works]`

**UX principles**

- Minimal cognitive load – one field per message, with examples.
- Clear feedback – errors mention *which* field is missing.
- Emotional engagement – positive tone (“you can now post deals customers see instantly”).

---

### 3.2 Creating a New Deal

Triggered by `/newdeal`, “Post a deal” button or menu entry.

#### Step 1 – Choose deal type (optional)

- Bot:
  > “What type of deal is this?”

  Reply keyboard:
  - `Ready-to-eat meals`
  - `Bakery`
  - `Fruits & veggies`
  - `Other`

This is for discovery later; not strictly required.

#### Step 2 – Offer basics

1. **Title**
   - “Short title (e.g. ‘Evening Veggie Box’).”
2. **Description**
   - “Quick description: what’s inside, any dietary notes (max 200 characters).”
3. **Photo**
   - “Send a photo of the produce or your venue (optional but recommended).”
4. **Time window**
   - Reply keyboard: `Today only`, `Today & tomorrow`, `Custom…`
     - For `Today only`:
       - Ask pickup start + end time (choose from small reply keyboard of common times or text).
     - For `Custom`:
       - Ask exact dates (text, validated).
5. **Quantity & price**
   - “How many units are available?” (number; validate >0)
   - “Price per unit (in €)” (number; validate precision & minimum >0).

At each step, we allow `/cancel` to abort and `/back` (custom handling) to go to previous field.

#### Step 3 – Summary & confirmation

Bot sends a **single composed message**:

> **Evening Veggie Box – 5€**  
> 🏪 *Business name*  
> 📍 *Address*  
> ⏰ *Today 18:00–21:00*  
> 📦 *Quantity:* 10  
> 📝 *Description:* “Mixed seasonal veg, best before tomorrow.”

Inline keyboard:

- `[Publish deal]`
- `[Edit field]` → opens a mini menu:
  - `Title`, `Description`, `Photo`, `Time window`, `Price`, `Quantity`
- `[Cancel]`

**Error handling before publish**

- If any required field still missing (bug, or user skipped):
  - Disable `[Publish deal]` and show:
    > “Missing: **quantity**. Tap ‘Edit field’ → Quantity to fix.”

#### Step 4 – Publishing

When user taps `[Publish deal]`:

1. Backend validates again:
   - Business is approved.
   - All fields present.
2. Creates `Offer` entity with state `ACTIVE`.
3. Bot edits summary message:
   > “✅ Deal published!  
   > Customers can see this until *21:00 today* or until it’s sold out.”

   Inline keyboard:
   - `[View as customer]`
   - `[Share link]`
   - `[Manage offer]`

`[Share link]` uses deep link `https://t.me/marketplace_bot?start=offer_<offer_id>`.

**Acceptance criteria coverage**

- Business can submit complete post → visible to customers (FR-001, FR-010).
- End time leads to auto expiry → bot updates offer state when expired (FR-004).

---

## 4. UX Flow for User Story 2 – Customer Views & Purchases a Deal (P1)

**Goal:** Customers discover an offer quickly (SC-003), buy with one clear “Buy” button (FR-003), receive confirmation and redemption instructions (FR-006), and we avoid overselling (FR-005, SC-004).

### 4.1 Entry Points for Customers

- `/start` → choose role `I’m a customer`.
- `/browse` command.
- Menu button → `Browse deals`.
- Deep link from shared deal: `?start=offer_<offer_id>`.
- (Optional later) Inline mode: `@marketplace_bot <city>` to share offers in group chats. :contentReference[oaicite:17]{index=17}  

### 4.2 Discovery Screen

**Message layout**

> “Here are deals near you 👇  
> (Use the buttons to filter or move between deals.)”

Reply keyboard (optional, transient):

- `Nearby`
- `All deals`
- `Ending soon`

Once a filter is chosen, we switch to inline keyboards for navigation.

**Offer card format**

For each offer:

> **Evening Veggie Box – 5€**  
> 🏪 *Business name*  
> 📍 *Address (short)*  
> ⏰ *Today 18:00–21:00*  
> 📦 *Left:* 7  

Inline keyboard:

- `[View details]`
- `[Buy]`
- Row below: `[Prev]` `[Next]` `[Back to filters]`

`[Prev]` / `[Next]` use callback data for pagination; we edit the current message text & keyboard instead of sending new messages, following Telegram’s recommendation for smoother UX. :contentReference[oaicite:18]{index=18}  

### 4.3 Offer Details

When customer taps `[View details]`:

> **Evening Veggie Box – 5€ each**  
> 🏪 *Business name*  
> 📍 *Full address*  
> ⏰ *Pickup:* Today 18:00–21:00  
> 📦 *Units left:* 7  
> 📝 *Description…*  

Inline keyboard:

- Quantity selector row:
  - `[-] 1 [+]`
- Action row:
  - `[Buy 1 for 5€]`
  - `[Back]`

Tapping `[-]` or `[+]` edits the message (not new chat spam), adjusting qty within available stock.

### 4.4 Purchase & Payment Flow

When `[Buy X for Y€]` is tapped:

1. **Reservation check (server side)**
   - Try to reserve `X` units:
     - If stock sufficient → create “pending purchase” with soft lock.
     - If not → return error (see edge cases below).

2. **Payment options**

   **Option A – Native Telegram Payments (recommended)**

   - Bot sends an invoice message with product photo, name, total price and prominent **Pay** button.
   - User taps **Pay**, sees Telegram’s payment sheet.
   - Telegram sends card & billing data directly to Stripe or another provider; bot never sees card details. :contentReference[oaicite:19]{index=19}  
   - On success:
     - Bot receives `successful_payment` update. :contentReference[oaicite:20]{index=20}  
     - Reserve is confirmed as paid, inventory decremented.

   **Option B – External hosted checkout**

   - Inline keyboard under the detail message:
     - `[Pay with card (opens Stripe)]` → URL button.
   - After redirect back (if you implement Web Login / deep link), bot marks purchase as paid.

3. **Confirmation message**

After successful payment:

> “🎉 Purchase confirmed!  
> **Evening Veggie Box – 1 unit**  
> 🧾 Order ID: *ABC123*  
> 📍 *Business name, full address*  
> ⏰ Pickup by: *Today 21:00*  
>  
> Show this message at the venue. The business might check your Order ID.”

Inline keyboard:

- `[View on map]` (URL to maps app)
- `[My purchases]`
- `[Share feedback]`

This supports FR-006 (confirmation + redemption instructions + reference ID).

---

### 4.5 Customer Views & Manages Purchases

Command `/my_purchases` or menu entry.

- Bot lists recent, non-expired purchases (cards like):

> **Evening Veggie Box – 1×**  
> Pickup by *Today 21:00*  
> Status: `Confirmed`

Inline keyboard per purchase:

- `[Show QR / code]` (optional)
- `[Cancel before pickup]` (if before end time; FR-013)
- `[Back]`

On cancellation:

- Bot confirms with yes/no.
- If `Yes` and before pickup window end:
  - Marks purchase as cancelled (no refund per spec).
  - Returns units to inventory.
  - Message:
    > “❌ Purchase cancelled.  
    > Note: No refund is provided, but your reserved unit is released for others.”

---

### 4.6 Edge Cases for Customers

1. **Overselling / race on last unit**
   - When user taps Buy:
     - Attempt to reserve atomically.
     - If another customer grabbed the last unit first:
       - Show message:
         > “😕 That was the last unit and someone just bought it.  
         > This deal is now sold out.”
       - Disable Buy buttons on all open offer messages (update inline keyboards).

2. **Offer expires during checkout**
   - Before sending invoice / payment URL:
     - Check current time ≤ offer end time.
   - If expired:
     > “This offer expired at *21:00*.  
     > You won’t be charged. Browse other deals instead.”
   - Do **not** send invoice.

3. **Paused / unpublished offers**
   - If callback from `[Buy]` arrives for a paused or unpublished offer:
     > “This offer is currently unavailable (paused by the business).  
     > Try another deal.”

4. **Malformed / ambiguous address (from business data)**
   - On customer side, we **never show broken addresses**:
     - If city or street missing → show generic text:
       > “Address unavailable – please contact the venue.”
     - And log for ops to fix.

---

## 5. UX Flow for User Story 3 – Offer Lifecycle Management (P2)

**Goal:** Let businesses pause, edit or end offers easily; customers always see the correct state (FR-007, FR-008, FR-009).

### 5.1 Entry: `/myoffers` or Menu → `My offers`

Bot message:

> “Your active offers 👇”

For each offer, a compact card:

> **Evening Veggie Box – 5€**  
> Status: `Active`  
> Units left: 7  
> Ends: *Today 21:00*

Inline keyboard:

- Row 1: `[Pause]` / `[Resume]` (depending on state)
- Row 2: `[Edit]` `[End now]` 
- Row 3: `[View as customer]`

### 5.2 Pause / Resume Offers

- Tap `[Pause]`:
  - Server marks offer `PAUSED`.
  - Bot **edits the offer card message**:
    - Status: `Paused`
    - Buttons: `[Resume]` `[View as customer]` (no Buy paths).
  - Bot also edits any customer-facing cards (where possible) to:
    - Add `⚠️ Paused` line.
    - Disable or remove `[Buy]` button.
  - Customer clicking an old Buy button gets:
    > “This offer is paused right now. The business might reopen it later.”

- Tap `[Resume]`:
  - Same as above, flipping back to `ACTIVE` if still before end time.

### 5.3 Edit Offer Fields

From offer card, `[Edit]`:

Inline keyboard of editable fields:

- `Price`
- `Quantity`
- `Time window`
- `Description`

Flow example for `Price`:

1. Bot:
   > “Current price: **5€**  
   > Send new price per unit (e.g. `4.50`).”

2. On valid price:
   - Update Offer.
   - Edit business view & customer cards to reflect new price.
   - Message:
     > “✅ Price updated to **4.50€**.”

For `Quantity`:

1. Bot:
   > “Current remaining: **7**.  
   > Send new remaining quantity (0–7).”

2. If set to 0:
   - Offer becomes `SOLD_OUT`.
   - Customer view:
     - Show `Sold out` badge.
     - Disable `[Buy]`.
   - This matches acceptance scenario: quantity zero → Sold Out.

### 5.4 End Offers Early

From offer card, `[End now]`:

- Safety confirmation:
  > “End this offer now? Customers won’t be able to buy it.  
  > This can’t be undone.”
- Inline keyboard: `[Yes, end now]` `[No]`
- On `Yes`:
  - State → `EXPIRED_EARLY`.
  - Business card: `Status: Ended early`.
  - Customer cards: show `Expired` label; remove `[Buy]`.

---

## 6. Error Messaging & Feedback Patterns

### 6.1 Global Patterns

- Always pair **error text** with **actionable suggestion**.
- Keep messages short; use emoji sparingly as status cues:
  - ✅ success
  - ⚠️ warning / soft error
  - ❌ hard error
- Use `/help` link in messages the first time the user hits an error.

### 6.2 Typical Errors

- **Missing required fields (business posting)**
  - “I still need the **pickup end time**. Send it like `21:00`.”

- **Invalid numeric input**
  - “That doesn’t look like a number. Send just the amount, e.g. `5` or `4.50`.”

- **Permissions**
  - “You need an approved business account to post deals.  
     Use `/register_business` first.”

- **System issues (e.g. payment provider down)**
  - “We couldn’t start checkout right now.  
     Your card hasn’t been charged. Please try again later.”

This supports FR-002, FR-009 and SC-002 (high success rate).

---

## 7. Mapping UX to Requirements & Success Criteria

### 7.1 Functional Requirements

- **FR-001 / FR-002** – Guided multi-step deal creation with validation before publish.
- **FR-003** – Offer cards always expose an explicit `[Buy]` / `[Pay]` button.
- **FR-004** – End time captured at creation; we check vs current time on all purchase attempts and on a scheduled job to auto-expire.
- **FR-005** – Reservation + finalization logic in purchase flow; oversell prevented through atomic operations and user sees clear messages when sold out.
- **FR-006** – Confirmation screen includes order ID, address, pickup window and instructions.
- **FR-007** – `/myoffers` & inline management buttons for pause/edit/end.
- **FR-008** – Each successful / cancelled purchase updates inventory and logs outcome.
- **FR-009** – Consistent, clear error messages for:

  - expired
  - sold out
  - paused
  - invalid inputs

- **FR-010** – Discovery via `/browse`, filters, and paginated offer cards.

- **FR-011** – Payments via Telegram’s interface backed by Stripe or external URL checkout (third-party provider).
- **FR-012** – Business registration, admin approval, and status messaging.
- **FR-013** – Cancellation flow available up to end time; after that, no cancellation option shown.

### 7.2 Success Criteria

- **SC-001 (business posts in under 2 minutes)**  
  - One field per step, examples, defaults for time ranges and categories, no complex screens.

- **SC-002 (95% purchase success)**  
  - Clear states, robust validation before initiating payment, easy to retry.

- **SC-003 (relevant deal in ≤10s)**  
  - `/browse` → immediate offer card; filters are optional, not required.

- **SC-004 (overselling ≤0.1%)**  
  - Reservation logic + explicit UX for “someone just bought the last one”.

- **SC-005 (clarity of purchase & redemption)**  
  - Confirmation message has all key info and consistent order layout.

---

## 8. Accessibility, Consistency, Emotional Tone

### 8.1 Accessibility

- Short sentences and everyday language.
- Avoid jargon like “pre-checkout query” in UI; keep that in backend docs.
- Color / emoji not required to understand the message (also use text labels).
- Support multiple languages by adapting texts to user’s `language_code`, as Telegram recommends. :contentReference[oaicite:21]{index=21}  

### 8.2 Consistency & Efficiency

- Same patterns for:
  - Detail + inline actions; 
  - Pagination (`[Prev]` / `[Next]`);
  - Back / Cancel buttons.
- Frequent tasks are 1–2 taps:
  - “Post deal” available in menu and after approval.
  - “Browse deals” always reachable via menu and `/browse`.

### 8.3 Emotional Engagement

- Copy leans into the “save food, save money” story:
  - “Nice catch! You just saved good food from going to waste 🍃”
- Positive reinforcement for businesses:
  - “Your deal is live – let’s get this food to hungry customers before closing time.”

---

## 9. Implementation Checklist (Telegram Side)

1. Configure bot commands & scopes with BotFather.
2. Implement `/start`, `/register_business`, `/newdeal`, `/myoffers`, `/browse`, `/my_purchases`, `/help`, `/settings`.
3. Build reply keyboards for:
   - Role selection.
   - Simple filters.
4. Build inline keyboard patterns for:
   - Deal summary & management.
   - Offer browsing & details.
   - Purchase and payment.
5. Implement deep link handling (`start=business_invite_*`, `start=offer_*`).
6. Integrate Payments:
   - Set provider (Stripe) and tokens.
   - Implement `sendInvoice`, `answerPreCheckoutQuery`, and `successful_payment` handlers.
7. Implement reservation + purchase confirmation logic.
8. Implement scheduled tasks to expire offers and refresh customer-facing cards.

---

If you’d like, next step I can do is turn this into:

- concrete **state diagrams**, or  
- a **message / callback spec** (including example JSON for reply_markup and typical updates),  

so your devs can go from “nice UX” to “actual bot”.
