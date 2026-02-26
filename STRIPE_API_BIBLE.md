# Stripe API Bible — Complete Reference

Everything a TAM needs to know about Stripe's API: architecture, authentication, error handling, pagination, and every major endpoint.

---

## Part 1: API Fundamentals

### Base URL

```
https://api.stripe.com/v1/
```

All requests are HTTPS only. Stripe uses REST with predictable resource-oriented URLs.

### Authentication

```bash
# Secret key (server-side only — NEVER expose in frontend)
curl https://api.stripe.com/v1/charges \
  -u sk_test_abc123:

# The colon after the key = empty password (HTTP Basic Auth)
```

```python
# Python SDK
import stripe
stripe.api_key = "sk_test_abc123"
```

### Key Types

| Key | Prefix | Use |
|-----|--------|-----|
| Secret key (test) | `sk_test_` | Server-side, test mode |
| Secret key (live) | `sk_live_` | Server-side, production |
| Publishable key (test) | `pk_test_` | Client-side (Stripe.js), test mode |
| Publishable key (live) | `pk_live_` | Client-side (Stripe.js), production |
| Restricted key | `rk_test_` / `rk_live_` | Limited permissions |

**Rule:** Secret keys on the server only. Publishable keys on the client only. Never mix them.

### API Versioning

```python
# Pin to a specific API version
stripe.api_version = "2024-06-20"

# Or set per-request
stripe.PaymentIntent.create(
    amount=1000,
    currency="eur",
    stripe_version="2024-06-20"
)
```

Stripe releases new API versions regularly. Pin your version to avoid breaking changes. Upgrade deliberately.

---

## Part 2: Request & Response Patterns

### Standard CRUD Operations

```python
# CREATE
customer = stripe.Customer.create(
    email="merchant@example.com",
    name="TechGear GmbH"
)

# READ (retrieve single)
customer = stripe.Customer.retrieve("cus_abc123")

# UPDATE
customer = stripe.Customer.modify(
    "cus_abc123",
    metadata={"plan": "scale"}
)

# DELETE
stripe.Customer.delete("cus_abc123")

# LIST (with filters)
customers = stripe.Customer.list(
    limit=10,
    created={"gte": 1700000000}  # Unix timestamp
)
```

### Expand — Get Related Objects in One Call

```python
# Without expand: charge.customer = "cus_abc123" (just the ID)
charge = stripe.Charge.retrieve("ch_xyz")

# With expand: charge.customer = full Customer object
charge = stripe.Charge.retrieve(
    "ch_xyz",
    expand=["customer", "balance_transaction"]
)

# On list endpoints
charges = stripe.Charge.list(
    limit=10,
    expand=["data.customer", "data.balance_transaction"]
)
```

**TAM tip:** Expand reduces API calls. Instead of fetching a charge then separately fetching the customer, do it in one call.

### Pagination

```python
# Auto-pagination (recommended)
for charge in stripe.Charge.list(limit=100).auto_paging_iter():
    print(charge.id)

# Manual pagination
charges = stripe.Charge.list(limit=100)
while charges.has_more:
    charges = stripe.Charge.list(
        limit=100,
        starting_after=charges.data[-1].id
    )
    for charge in charges.data:
        print(charge.id)
```

| Parameter | What it does |
|-----------|-------------|
| `limit` | Max items per page (1-100, default 10) |
| `starting_after` | Cursor: fetch items after this ID |
| `ending_before` | Cursor: fetch items before this ID |
| `created[gte]` | Filter: created on or after (Unix timestamp) |
| `created[lte]` | Filter: created on or before |

### Metadata — Custom Key-Value Pairs

```python
# Add metadata to any object (up to 50 keys, 500 char values)
pi = stripe.PaymentIntent.create(
    amount=34900,
    currency="eur",
    metadata={
        "order_id": "NB-12345",
        "customer_email": "anna@techgear.de",
        "product": "nordbrew_pro_3000",
        "channel": "web"
    }
)

# Update metadata (merges, doesn't replace)
stripe.PaymentIntent.modify(
    pi.id,
    metadata={"shipped": "true"}
)

# Remove a metadata key (set to empty string)
stripe.PaymentIntent.modify(
    pi.id,
    metadata={"shipped": ""}
)
```

**TAM tip:** Metadata is searchable in Dashboard and Sigma. Always recommend merchants tag payments with order_id, customer_email, and product.

---

## Part 3: Error Handling

### Error Types

| HTTP Code | Error Type | Meaning | Retry? |
|-----------|-----------|---------|--------|
| 400 | `InvalidRequestError` | Bad parameters | No — fix the request |
| 401 | `AuthenticationError` | Bad API key | No — check credentials |
| 402 | `CardError` | Card declined | Depends on decline code |
| 403 | `PermissionError` | Key lacks permission | No — use correct key |
| 404 | `InvalidRequestError` | Resource not found | No — check the ID |
| 409 | `IdempotencyError` | Key reused with different params | No — use new key |
| 429 | `RateLimitError` | Too many requests | Yes — backoff and retry |
| 500 | `APIError` | Stripe server error | Yes — retry with backoff |
| 502 | `APIConnectionError` | Network issue | Yes — retry with backoff |
| 503 | `APIError` | Stripe overloaded | Yes — retry with backoff |

### Error Handling in Python

```python
try:
    pi = stripe.PaymentIntent.create(
        amount=10000,
        currency="eur",
        payment_method="pm_card_visa",
        confirm=True
    )
except stripe.error.CardError as e:
    # Card was declined
    decline_code = e.error.decline_code
    message = e.user_message
    print(f"Card declined: {decline_code} — {message}")

except stripe.error.RateLimitError:
    # Too many requests — implement backoff
    print("Rate limited — retry after delay")

except stripe.error.InvalidRequestError as e:
    # Bad parameters
    print(f"Invalid request: {e}")

except stripe.error.AuthenticationError:
    # Wrong API key
    print("Check your API key")

except stripe.error.APIConnectionError:
    # Network issue
    print("Network error — retry")

except stripe.error.StripeError as e:
    # Catch-all for other Stripe errors
    print(f"Stripe error: {e}")
```

### Decline Codes (CardError)

| Code | Meaning | TAM Action |
|------|---------|------------|
| `insufficient_funds` | Customer's bank says no funds | Suggest alternative payment method |
| `card_declined` | Generic decline from issuer | Customer should contact bank |
| `expired_card` | Card is expired | Enable automatic card updater |
| `incorrect_cvc` | Wrong CVC entered | Customer should re-enter |
| `processing_error` | Temporary processing issue | Safe to retry |
| `stolen_card` | Issuer flagged as stolen | Do NOT retry, flag for review |
| `fraudulent` | Issuer suspects fraud | Do NOT retry |
| `do_not_honor` | Issuer won't say why | Customer should contact bank |
| `authentication_required` | SCA/3DS needed | Trigger 3DS flow |
| `try_again_later` | Temporary issue | Retry after 1-2 seconds |

### Rate Limits

| Mode | Limit |
|------|-------|
| Test mode | 25 requests/second |
| Live mode | 100 requests/second |

```python
# Exponential backoff for rate limits
import time
import random

def call_with_backoff(func, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(**kwargs)
        except stripe.error.RateLimitError:
            delay = (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(delay)
    raise Exception("Max retries exceeded")
```

---

## Part 4: Idempotency

```python
# Same key = same result (within 24 hours)
pi = stripe.PaymentIntent.create(
    amount=10000,
    currency="eur",
    idempotency_key="order_12345_payment"
)

# Retry with same key = returns cached result, no duplicate
pi_retry = stripe.PaymentIntent.create(
    amount=10000,
    currency="eur",
    idempotency_key="order_12345_payment"
)
# pi.id == pi_retry.id (same PaymentIntent!)
```

| Rule | Detail |
|------|--------|
| Keys expire after 24 hours | After that, same key creates new resource |
| Same key + different params = error | `IdempotencyError` (409) |
| Only for POST requests | GET, DELETE are naturally idempotent |
| Key format | Any string up to 255 chars |
| Best practice | Use composite: `{order_id}_{action}` |

---

## Part 5: PaymentIntents API (Most Important)

### Lifecycle

```
create -> requires_payment_method
       -> requires_confirmation
       -> requires_action (3DS)
       -> processing
       -> succeeded / requires_capture / canceled
```

### Create & Confirm

```python
# Step 1: Create (server-side)
pi = stripe.PaymentIntent.create(
    amount=34900,      # EUR 349.00 (always in cents!)
    currency="eur",
    automatic_payment_methods={"enabled": True},
    metadata={"order_id": "NB-12345"}
)
# Returns client_secret for frontend

# Step 2: Confirm (can be server or client-side)
pi = stripe.PaymentIntent.confirm(
    pi.id,
    payment_method="pm_card_visa",
    return_url="https://yoursite.com/success"
)

# Or create + confirm in one call
pi = stripe.PaymentIntent.create(
    amount=34900,
    currency="eur",
    payment_method="pm_card_visa",
    confirm=True,
    automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
)
```

### Capture (for auth-and-capture flow)

```python
# Create with capture_method="manual"
pi = stripe.PaymentIntent.create(
    amount=34900,
    currency="eur",
    capture_method="manual",  # Auth only, capture later
    payment_method="pm_card_visa",
    confirm=True
)
# Status: requires_capture

# Capture (within 7 days)
stripe.PaymentIntent.capture(pi.id)
# Can capture partial: capture(pi.id, amount_to_capture=20000)
```

### Cancel

```python
stripe.PaymentIntent.cancel(
    pi.id,
    cancellation_reason="requested_by_customer"
)
```

### Search PaymentIntents

```python
# Search by metadata
results = stripe.PaymentIntent.search(
    query="metadata['order_id']:'NB-12345'"
)

# Search by status and amount
results = stripe.PaymentIntent.search(
    query="status:'succeeded' AND amount>10000"
)

# Search by date range
results = stripe.PaymentIntent.search(
    query="created>1700000000 AND created<1702000000"
)
```

---

## Part 6: Other Key Endpoints

### Customers

```python
# Create
customer = stripe.Customer.create(
    email="anna@techgear.de",
    name="Anna Mueller",
    metadata={"company": "TechGear GmbH"}
)

# Attach payment method
stripe.PaymentMethod.attach(
    "pm_card_visa",
    customer=customer.id
)

# Set default payment method
stripe.Customer.modify(
    customer.id,
    invoice_settings={"default_payment_method": "pm_card_visa"}
)
```

### Refunds

```python
# Full refund
refund = stripe.Refund.create(
    payment_intent="pi_abc123"
)

# Partial refund
refund = stripe.Refund.create(
    payment_intent="pi_abc123",
    amount=5000  # EUR 50.00
)

# Refund with reason and metadata
refund = stripe.Refund.create(
    payment_intent="pi_abc123",
    reason="requested_by_customer",
    metadata={"ticket": "SUPPORT-456"}
)
```

### Disputes

```python
# List open disputes
disputes = stripe.Dispute.list(limit=20)

# Submit evidence
stripe.Dispute.modify(
    "dp_abc123",
    evidence={
        "customer_email_address": "customer@example.com",
        "shipping_tracking_number": "DHL-123456789",
        "shipping_carrier": "DHL",
        "shipping_date": "2026-01-15",
        "uncategorized_text": "Order shipped and delivered on Jan 17."
    },
    submit=True  # False = save as draft
)
```

### Balance

```python
# Current balance
balance = stripe.Balance.retrieve()
# balance.available[0].amount = available funds (cents)
# balance.pending[0].amount = pending funds

# Balance transactions (every money movement)
txns = stripe.BalanceTransaction.list(
    limit=20,
    type="charge",
    created={"gte": 1700000000}
)
```

### Payouts

```python
# List payouts
payouts = stripe.Payout.list(limit=10)

# Create manual payout
payout = stripe.Payout.create(
    amount=100000,  # EUR 1000.00
    currency="eur"
)
```

---

## Part 7: Test Cards

| Card Number | Scenario |
|-------------|----------|
| `4242 4242 4242 4242` | Succeeds |
| `4000 0000 0000 0002` | Declined (generic) |
| `4000 0000 0000 9995` | Declined: `insufficient_funds` |
| `4000 0000 0000 9987` | Declined: `lost_card` |
| `4000 0000 0000 0069` | Declined: `expired_card` |
| `4000 0000 0000 0127` | Declined: `incorrect_cvc` |
| `4000 0027 6000 3184` | Requires 3DS authentication |
| `4000 0000 0000 3220` | 3DS required, always succeeds |
| `4000 0000 0000 0341` | Attaching to customer fails |
| `4000 0000 0000 3063` | 3DS required, always fails |

```python
# Use test payment methods by token
payment_method = "pm_card_visa"          # Visa success
payment_method = "pm_card_chargeDeclined" # Generic decline
```

### Test Tokens for Payment Methods

| Token | Method |
|-------|--------|
| `pm_card_visa` | Visa |
| `pm_card_mastercard` | Mastercard |
| `pm_card_amex` | American Express |
| `pm_card_sepaDebit` | SEPA Direct Debit |

---

## Part 8: API Best Practices for TAMs

### What to Recommend to Merchants

1. **Always use PaymentIntents** — not the legacy Charges API
2. **Always use idempotency keys** — for any write operation
3. **Always handle webhooks** — don't poll for status
4. **Always expand related objects** — reduces API calls
5. **Always use metadata** — tag everything with order_id
6. **Always pin API version** — avoid surprise breaking changes
7. **Always use test mode first** — then switch to live keys
8. **Never log full API keys** — mask them in logs
9. **Never expose secret keys** — client-side = publishable only
10. **Never store card numbers** — use Stripe.js / Elements

### Common Mistakes Merchants Make

| Mistake | Impact | Fix |
|---------|--------|-----|
| Using Charges API instead of PaymentIntents | No SCA/3DS support | Migrate to PaymentIntents |
| No webhook signature verification | Vulnerable to fake events | Use `construct_event()` |
| Polling instead of webhooks | Wasted API calls, missed events | Implement webhook listeners |
| No idempotency keys | Duplicate charges on retry | Add composite keys |
| Hardcoded currency | Lost conversion in multi-market | Detect customer locale |
| No error handling | Silent failures | Catch all StripeError types |
| Logging full API keys | Security breach | Mask keys, use env vars |
| Not expanding objects | Extra API calls | Use expand parameter |

---

*All amounts in Stripe are in the smallest currency unit (cents for EUR/USD). Always divide by 100.0 for display.*
