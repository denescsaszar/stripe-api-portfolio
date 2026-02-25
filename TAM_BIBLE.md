# The Stripe TAM Bible

A comprehensive reference guide covering Stripe fundamentals, mental models, and TAM diagnostic patterns for interview preparation and real-world merchant support.

---

## Table of Contents

1. [TAM Mindset](#tam-mindset)
2. [Core Concepts](#core-concepts)
3. [Webhooks: Event-Driven Architecture](#webhooks-event-driven-architecture)
4. [PaymentIntents: The Modern Payment Flow](#paymentintents-the-modern-payment-flow)
5. [Subscriptions & Billing](#subscriptions--billing)
6. [Payouts & Balance](#payouts--balance)
7. [Disputes & Chargebacks](#disputes--chargebacks)
8. [Stripe Connect](#stripe-connect)
9. [Radar: Fraud Detection](#radar-fraud-detection)
10. [Common TAM Patterns](#common-tam-patterns)
11. [Test Cards & Scenarios](#test-cards--scenarios)
12. [TAM Debugging Checklist](#tam-debugging-checklist)

---

## TAM Mindset

### Your Role

A **Technical Account Manager** at Stripe is not a salesperson. You're a trusted advisor who:

- Understands merchant pain points before they escalate
- Translates Stripe features into merchant language
- Diagnoses root causes, not just symptoms
- Builds long-term relationships by solving real problems
- Anticipates merchant needs and educates proactively

### The TAM Diagnostic Framework

When a merchant says "payments are failing":

1. **Understand the Impact** — How many customers? How much revenue? What's the deadline?
2. **Gather Facts** — Error codes, timestamps, card types, geographic patterns, test vs. production
3. **Categorize Root Cause** — Is it Stripe? Merchant code? Acquirer? Customer behavior?
4. **Recommend a Solution** — With context, not just documentation links
5. **Enable Their Team** — Leave them confident, not dependent

### Communication Patterns

**Don't say:** "You need to implement webhook retries."

**Do say:** "Stripe will deliver webhooks multiple times—some merchants miss critical events. I recommend storing events in a queue and processing them reliably. Here's a pattern that works well..."

**Don't say:** "Your integration doesn't support 3DS."

**Do say:** "To reach customers in Europe, you'll need Strong Customer Authentication. The good news: Stripe handles it automatically with PaymentIntents. Here's what your flow will look like..."

---

## Core Concepts

### The Stripe Payment Lifecycle

```
Customer → Merchant → Stripe API → Card Networks → Banks → Customer's Bank
```

At each stage, something can fail. Your job: identify where.

### Idempotency

**Rule:** Every API call should include `idempotency_key` to prevent duplicate charges if the request is retried.

```python
stripe.PaymentIntent.create(
    amount=1000,
    currency="usd",
    payment_method="pm_card_visa",
    confirm=True,
    idempotency_key="merchant_order_12345"  # Same key = same result
)
```

**Why merchants forget this:** They only think about it after duplicate charges happen.

### Error Code Classification

Stripe error codes fall into three categories:

| Category            | Example                                      | Merchant Action                                        |
| ------------------- | -------------------------------------------- | ------------------------------------------------------ |
| **TEMPORARY**       | `rate_limit_error`, `api_connection_error`   | Retry with exponential backoff (safe)                  |
| **PERMANENT**       | `card_declined`, `expired_card`              | Customer action needed (different card, update expiry) |
| **ACTION_REQUIRED** | `authentication_required`, `requires_action` | 3DS/SCA challenge or confirmation                      |

**Common mistake:** Merchants retry `card_declined` forever. Don't. Show the customer a better card form.

### Test Mode vs. Live Mode

- **Test mode:** Stripe returns predictable results. Use test cards like `4242424242424242`.
- **Live mode:** Real charges. Real money. One `stripe_user_id` per merchant account.

**TAM tip:** Always ask "are you testing this in test mode first?" before suggesting live implementation.

---

## Webhooks: Event-Driven Architecture

### Mental Model: Doorbell vs. Knocking

**API polling (bad):** You knock on Stripe's door every 10 seconds asking "did anything happen?" (Inefficient, delayed, expensive)

**Webhooks (good):** Stripe rings your doorbell when something happens. You answer immediately. (Efficient, real-time, reliable)

### How Webhooks Work

1. **Merchant registers endpoint** with Stripe (e.g., `https://api.mystore.com/webhooks/stripe`)
2. **Event happens** (e.g., `charge.succeeded`)
3. **Stripe sends POST request** to the endpoint with event data
4. **Merchant processes event** (e.g., fulfill order, send receipt)
5. **Merchant returns 200 OK** to confirm receipt
6. **Stripe marks event as delivered** (or retries if no 200)

### Stripe's Retry Logic

- Immediate retry (5 seconds)
- 5 minutes later
- 30 minutes later
- 2 hours later
- 5 hours later
- 10 hours later
- 24 hours later

**Total window:** ~48 hours. After that, the event is marked as abandoned.

### Events Merchants Must Handle

| Event                            | When                 | Merchant Action        |
| -------------------------------- | -------------------- | ---------------------- |
| `payment_intent.succeeded`       | Charge succeeded     | Fulfill order          |
| `payment_intent.payment_failed`  | Charge failed        | Notify customer        |
| `payment_intent.requires_action` | 3DS/SCA needed       | Show authentication UI |
| `charge.refunded`                | Refund processed     | Credit account         |
| `charge.dispute.created`         | Chargeback filed     | Prepare evidence       |
| `customer.subscription.updated`  | Subscription changed | Sync to internal DB    |

### Webhook Security

**Always verify webhook signatures:**

```python
import stripe

endpoint_secret = "whsec_..."

@app.route('/webhooks/stripe', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    # Process event
    if event['type'] == 'charge.succeeded':
        process_successful_charge(event['data']['object'])

    return "Received", 200
```

### Common Webhook Problems

**Problem:** "We're not receiving webhooks"

**Diagnosis:**

1. Is the endpoint registered in Dashboard > Developers > Webhooks?
2. Is the endpoint accessible from the internet?
3. Is Stripe blocked by a firewall?
4. Are you returning 200 OK?
5. Check webhook logs in Dashboard for failed delivery attempts

**Solution:** Implement webhook reliability:

```python
# Store event in database FIRST
event_record = WebhookEvent.create(event_id=event['id'], data=event)

# Process SECOND
try:
    process_event(event)
    event_record.mark_processed()
except Exception as e:
    event_record.mark_failed(error=str(e))
    # Job queue will retry
    return "Processing error", 500  # Stripe will retry

return "Processed", 200
```

---

## PaymentIntents: The Modern Payment Flow

### Why PaymentIntents (Not Charges API)

**Old way (Charges API):**

```
Merchant → Token card → Create charge → Done (or SCA error)
```

**Problem:** Merchant handles SCA/3DS manually. Complicated. Error-prone. Not PSD2-compliant in EU.

**New way (PaymentIntents):**

```
Merchant → Create PaymentIntent → Stripe determines if 3DS needed → Confirm → Done
```

**Benefit:** Stripe handles 3DS automatically. One flow for all scenarios.

### PaymentIntent Lifecycle

```
REQUIRES_PAYMENT_METHOD → REQUIRES_CONFIRMATION → REQUIRES_ACTION → SUCCEEDED
                                                    ↓
                                                (3DS needed)
```

### Basic Flow

```python
import stripe

# Step 1: Create PaymentIntent
intent = stripe.PaymentIntent.create(
    amount=2000,  # $20.00 in cents
    currency="usd",
    payment_method="pm_card_visa",
    confirm=True,  # Immediately confirm
    return_url="https://mystore.com/checkout/success"  # For 3DS redirects
)

# Step 2: Check status
if intent.status == "succeeded":
    # Charge successful, fulfill order
    fulfill_order(order_id)

elif intent.status == "requires_action":
    # 3DS needed, send client_secret to frontend
    return {
        "client_secret": intent.client_secret,
        "status": "requires_action"
    }

elif intent.status == "processing":
    # Charge is pending (check back later)
    mark_order_as_pending(order_id)
```

### Frontend: Handling 3DS

```javascript
// Backend sends client_secret
const { client_secret, status } = response;

if (status === "requires_action") {
  // Show 3DS authentication
  const result = await stripe.confirmCardPayment(client_secret, {
    payment_method: {
      card: cardElement,
      billing_details: { name: "Jenny Rosen" },
    },
  });

  if (result.paymentIntent.status === "succeeded") {
    // 3DS passed, order complete
    showSuccess("Payment successful");
  } else {
    showError("3DS authentication failed");
  }
}
```

### Webhook Handling for PaymentIntents

```python
@app.route('/webhooks/stripe', methods=['POST'])
def webhook():
    event = verify_and_construct_event(request)

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        fulfill_order(intent.metadata.order_id)

    elif event['type'] == 'payment_intent.payment_failed':
        intent = event['data']['object']
        notify_customer_payment_failed(intent.metadata.order_id)

    elif event['type'] == 'payment_intent.requires_action':
        # This shouldn't happen if client_secret was handled correctly
        # But if it does, retry 3DS
        pass

    return "Received", 200
```

### Key PaymentIntent Fields

| Field            | Purpose                                                 |
| ---------------- | ------------------------------------------------------- |
| `amount`         | Charge amount in smallest currency unit (cents for USD) |
| `currency`       | 3-letter code (usd, eur, gbp)                           |
| `payment_method` | Card/bank account to charge                             |
| `confirm`        | Immediately attempt charge (vs. deferring)              |
| `off_session`    | Charge without customer present (subscription, invoice) |
| `customer`       | Link to Stripe Customer object                          |
| `metadata`       | Your custom data (order_id, user_id, etc.)              |
| `return_url`     | Where to send customer after 3DS (for web redirects)    |

---

## Subscriptions & Billing

### Subscription Lifecycle

```
TRIALING/ACTIVE → PAST_DUE → CANCELED
                      ↓
                  (retry logic)
```

### Creating a Subscription

```python
import stripe

# Step 1: Create or retrieve customer
customer = stripe.Customer.create(
    email="customer@example.com",
    payment_method="pm_card_visa",
    invoice_settings={"default_payment_method": "pm_card_visa"}
)

# Step 2: Create subscription
subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[{"price": "price_monthly_plan"}],
    billing_cycle_anchor=int(time.time()),  # Align all customers to same day
    expand=["latest_invoice.payment_intent"]
)
```

### Smart Retry Logic for Failed Invoices

**The problem:** Declined card during subscription renewal. Stripe retries automatically, but what if customer added a new card to their Stripe Customer profile?

**Smart approach:**

```python
@app.route('/webhooks/stripe', methods=['POST'])
def webhook():
    event = verify_and_construct_event(request)

    if event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        subscription = stripe.Subscription.retrieve(invoice.subscription)

        # Try to charge with the default payment method on file
        customer = stripe.Customer.retrieve(invoice.customer)

        if customer.invoice_settings.default_payment_method:
            # Retry with updated payment method
            try:
                stripe.Invoice.pay(invoice.id)
                notify_customer_payment_retry_succeeded(customer.email)
            except stripe.error.CardError as e:
                notify_customer_payment_failed(customer.email, str(e))
        else:
            # No payment method on file
            notify_customer_update_payment_method(customer.email)

    return "Received", 200
```

### Invoice States

| State           | Meaning                                       |
| --------------- | --------------------------------------------- |
| `draft`         | Created but not finalized                     |
| `open`          | Awaiting payment                              |
| `paid`          | Successfully charged                          |
| `uncollectible` | All retry attempts failed, marked as bad debt |
| `void`          | Explicitly canceled                           |

### Common Subscription Issues

**Problem:** "Customer was charged but invoice says unpaid"

**Diagnosis:**

- Check `invoice.payment_intent.status`
- Is the PaymentIntent status `succeeded`?
- If yes, update invoice manually: `stripe.Invoice.pay(invoice.id)`

**Problem:** "Subscription renewal is happening on the wrong day"

**Root cause:** Different customers have different billing cycle anchors. Use `billing_cycle_anchor` to align:

```python
stripe.Subscription.create(
    customer=customer.id,
    items=[{"price": "price_plan"}],
    billing_cycle_anchor=1609459200  # All customers renew on same day
)
```

---

## Payouts & Balance

### Balance States

```
AVAILABLE BALANCE: Ready to pay out (default 2-day hold)
    ↓
PENDING BALANCE: Waiting for hold to lift (fraud review, chargeback risk)
    ↓
PAYOUT: Transferred to bank account
```

### Understanding Holds

**Automatic holds (Stripe's default):**

- 2-day hold on card charges (fraud prevention)
- 7-day hold if disputes are filed
- Extended hold for high-risk merchants (payment volume, chargeback rate, industry)

**Merchant's perspective:** "Why can't I withdraw my money?"

**Your job:** Explain that holds are protective, show the payout schedule in Dashboard, clarify when money becomes available.

### Retrieving Balance

```python
import stripe

# Get current balance
balance = stripe.Balance.retrieve()

# Available balance (can payout immediately)
available = balance['available'][0]  # [0] = first currency
print(f"Available: {available['amount'] / 100} {available['currency'].upper()}")

# Pending balance (waiting for hold)
pending = balance['pending'][0]
print(f"Pending: {pending['amount'] / 100} {pending['currency'].upper()}")
```

### Payout Diagnostics

```python
# List recent payouts
payouts = stripe.Payout.list(limit=10)

for payout in payouts['data']:
    print(f"Payout {payout.id}:")
    print(f"  Amount: {payout.amount / 100} {payout.currency.upper()}")
    print(f"  Status: {payout.status}")
    print(f"  Arrival Date: {datetime.fromtimestamp(payout.arrival_date)}")
    print(f"  Type: {payout.type}")  # bank_account, card

    if payout.status == 'failed':
        print(f"  Failure Code: {payout.failure_code}")
        print(f"  Failure Reason: {payout.failure_reason}")
```

### Common Payout Issues

**Problem:** "Payout failed. Now what?"

**Diagnosis:**

1. Check `payout.failure_code` (usually `account_closed`, `debit_not_authorized`, `insufficient_funds`)
2. Ask merchant: Is the bank account still active? Has it been closed?
3. Suggest adding a new bank account in Dashboard

**Problem:** "My balance shows $0 but I made sales today"

**Root cause:** 2-day hold. Charge came in this morning, becomes available in 2 days.

**Solution:** Show the balance breakdown, explain the hold timeline, reassure that money is coming.

---

## Disputes & Chargebacks

### Chargeback Lifecycle

```
Customer files dispute with bank
    ↓
Stripe notifies merchant (charge.dispute.created)
    ↓
Merchant has 7-10 days to submit evidence
    ↓
Bank issues temporary credit to customer (chargeback)
    ↓
Stripe removes amount from merchant balance
    ↓
Bank reviews evidence and makes final decision
```

### Dispute States

| State                    | Meaning                              |
| ------------------------ | ------------------------------------ |
| `warning_needs_response` | Chargeback filed, evidence due soon  |
| `warning_under_review`   | Evidence submitted, waiting for bank |
| `won`                    | Bank sided with merchant             |
| `lost`                   | Bank sided with customer             |

### Submitting Evidence

```python
import stripe

# Retrieve dispute
dispute = stripe.Dispute.retrieve("dp_...")

# Submit evidence
evidence = stripe.Dispute.submit_evidence(
    "dp_...",
    evidence={
        "access_activity_log": "file_...",  # Stripe File ID
        "billing_address": "123 Main St",
        "cancellation_policy": "file_...",
        "customer_communication": "file_...",
        "customer_email_address": "customer@example.com",
        "customer_name": "Jenny Rosen",
        "product_description": "Online course on painting",
        "receipt": "file_...",
        "refund_policy": "file_..."
    }
)
```

### Evidence Types (Depending on Dispute Reason)

| Reason                  | Key Evidence                                                   |
| ----------------------- | -------------------------------------------------------------- |
| `fraudulent`            | IP address, device fingerprint, customer verification          |
| `unrecognized`          | Proof of delivery, customer communication, refund confirmation |
| `duplicate`             | Invoice showing single charge, refund confirmation             |
| `subscription_canceled` | Cancellation request, customer communication                   |

### TAM Advice for Merchants

**Prevention is better than cure:**

1. Send order confirmations immediately (proof of intent)
2. Use distinctive merchant name (prevent "unrecognized" disputes)
3. Clear refund policy on website
4. Process refunds quickly for legitimate requests (cheaper than chargeback)
5. Use AVS (Address Verification Service) and CVC checks

**During a dispute:**

1. Don't argue with the customer in evidence submission (tone matters)
2. Submit evidence early (don't wait until last day)
3. Include customer communication proving awareness/satisfaction
4. Provide timestamps and transaction IDs

---

## Stripe Connect

### Three Types of Accounts

| Type         | Use Case                            | Merchant Controls                                     |
| ------------ | ----------------------------------- | ----------------------------------------------------- |
| **Standard** | Individual freelancer, small seller | Full control of Dashboard, payment methods, payouts   |
| **Express**  | Marketplace seller                  | Limited Dashboard, Stripe handles payouts, compliance |
| **Custom**   | Advanced marketplace                | Merchant builds full UX, Stripe handles money flow    |

### Express Account Onboarding

```python
import stripe

# Create Express account
account = stripe.Account.create(
    type="express",
    country="US",
    email="seller@example.com",
    business_type="individual",  # or 'sole_prop', 'partnership', 'corporation'
)

# Generate onboarding link (seller completes in browser)
link = stripe.AccountLink.create(
    account=account.id,
    type="account_onboarding",
    return_url="https://mymarketplace.com/seller/onboarded",
    refresh_url="https://mymarketplace.com/seller/refresh"
)

print(f"Seller completes onboarding here: {link.url}")
```

### Requirements & Verification

Stripe may ask sellers to provide:

- SSN / Tax ID
- Business address
- Bank account details
- ID verification

**Check requirements status:**

```python
account = stripe.Account.retrieve(account.id)

for requirement in account.requirements['currently_due']:
    print(f"Seller must provide: {requirement}")

for verification in account.requirements['eventually_due']:
    print(f"Seller will eventually need: {verification}")
```

### Payouts for Connect Sellers

```python
# Payout Express account seller
payout = stripe.Payout.create(
    amount=5000,  # $50.00
    currency="usd",
    stripe_account=connected_account_id
)
```

### Common Connect Issues

**Problem:** "Seller's account is restricted. They can't receive payouts."

**Diagnosis:**

1. Check `account.charges_enabled` (is seller allowed to charge?)
2. Check `account.payouts_enabled` (is seller allowed to receive payouts?)
3. Check `account.requirements.currently_due` (what's missing?)

**Solution:**

- Ask seller to complete requirements
- Provide link to their onboarding flow if incomplete

**Problem:** "I created an Express account but seller says they can't see anything in their Dashboard"

**Root cause:** Express accounts have limited Dashboard access by design. They see a simplified interface.

**Solution:** If seller needs more control, suggest upgrading to Standard account (more responsibility, more control).

---

## Radar: Fraud Detection

### Risk Score (0-100)

Stripe analyzes every charge and assigns a risk score:

```
0-25:   Very low risk (most legitimate purchases)
26-50:  Low risk
51-75:  Medium risk (review or require 3DS)
76-100: High risk (block)
```

### Accessing Risk Score

```python
import stripe

# Create charge and get risk score
charge = stripe.Charge.create(
    amount=2000,
    currency="usd",
    source="tok_visa"
)

# Risk score is in the charge object
print(f"Risk Score: {charge.fraud_details}")

# For PaymentIntent:
intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    payment_method="pm_card_visa",
    confirm=True
)

# Risk score data is in related charge
charge = stripe.Charge.retrieve(intent.charges.data[0].id)
print(f"Risk: {charge.fraud_details}")
```

### Custom Radar Rules

**Use case:** Block purchases from specific countries

```python
# Create rule in Stripe Dashboard or via API
rule = stripe.radar.RadarRule.create(
    type="block",
    predicate={
        "type": "ip_country",
        "country": "XX"  # Country code
    }
)
```

**Use case:** Require 3DS for high-risk countries

```python
rule = stripe.radar.RadarRule.create(
    type="require_authentication",
    predicate={
        "type": "card_country",
        "country": ["CN", "RU", "KP"]  # Require 3DS for these countries
    }
)
```

**Use case:** Block high-value purchases from new customers\*\*

```python
rule = stripe.radar.RadarRule.create(
    type="block",
    predicate={
        "type": "and",
        "predicates": [
            {
                "type": "charge_amount",
                "condition": {
                    "gte": 50000  # $500+
                }
            },
            {
                "type": "customer_lifetime_value",
                "condition": {
                    "lte": 1000  # Customer has spent less than $10 lifetime
                }
            }
        ]
    }
)
```

### Trade-Off: Block vs. 3DS

**Block Rule:**

- Pro: Maximum fraud prevention
- Con: Legitimate customers get rejected (false positives)

**Require 3DS Rule:**

- Pro: Reduce fraud without outright rejection
- Con: Customer must complete authentication (friction)

**Best practice:** Start with require_authentication. Only block if attacks continue.

---

## Common TAM Patterns

### Pattern 1: The Webhook Listener

```python
from flask import Flask, request
import stripe
import json

app = Flask(__name__)
STRIPE_WEBHOOK_SECRET = "whsec_..."

@app.route('/webhooks/stripe', methods=['POST'])
def webhook_handler():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('stripe-signature')

    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    # Log event
    print(f"Event type: {event['type']}")

    # Route to handler
    handlers = {
        'charge.succeeded': handle_charge_succeeded,
        'charge.failed': handle_charge_failed,
        'charge.dispute.created': handle_dispute,
        'payment_intent.requires_action': handle_3ds_needed,
    }

    if event['type'] in handlers:
        handlers[event['type']](event['data']['object'])

    return "Received", 200

def handle_charge_succeeded(charge):
    print(f"Charge succeeded: {charge.id}")
    # Fulfill order, send receipt, etc.

def handle_charge_failed(charge):
    print(f"Charge failed: {charge.id}, reason: {charge.failure_reason}")
    # Notify customer, suggest retry

def handle_dispute(dispute):
    print(f"Dispute created: {dispute.id}")
    # Alert merchant, prepare evidence

def handle_3ds_needed(intent):
    print(f"3DS needed for {intent.id}")
    # Send client_secret to frontend
```

### Pattern 2: Retry Logic with Exponential Backoff

```python
import time
import stripe

def charge_with_retry(amount, currency, payment_method, max_retries=3):
    """Charge with automatic retry for temporary errors"""

    for attempt in range(max_retries):
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency=currency,
                source=payment_method,
                idempotency_key=f"charge_{payment_method}_{int(time.time())}"
            )
            return {"success": True, "charge": charge}

        except stripe.error.RateLimitError:
            # Too many requests, backoff
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"Rate limited. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

        except stripe.error.APIConnectionError:
            # Network error, backoff
            wait_time = 2 ** attempt
            print(f"Connection error. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

        except stripe.error.CardError as e:
            # Card declined (permanent error, don't retry)
            return {
                "success": False,
                "error": e.user_message,
                "code": e.code
            }

    return {"success": False, "error": "Max retries exceeded"}
```

### Pattern 3: Error Code Classifier

```python
def classify_error(error):
    """Classify Stripe error by retry strategy"""

    TEMPORARY_ERRORS = [
        'rate_limit_error',
        'api_connection_error',
        'api_error'
    ]

    PERMANENT_ERRORS = [
        'card_declined',
        'expired_card',
        'incorrect_cvc'
    ]

    ACTION_REQUIRED_ERRORS = [
        'authentication_required',
        'requires_action'
    ]

    error_type = error.__class__.__name__
    error_code = getattr(error, 'code', None)

    if error_code in TEMPORARY_ERRORS:
        return "RETRY"  # Safe to retry
    elif error_code in PERMANENT_ERRORS:
        return "CUSTOMER_ACTION"  # Customer must fix
    elif error_code in ACTION_REQUIRED_ERRORS:
        return "3DS_REQUIRED"  # Show authentication UI
    else:
        return "UNKNOWN"  # Investigate manually
```

### Pattern 4: Idempotency in Production

```python
import stripe
import hashlib

def create_charge_idempotent(order_id, amount, currency, payment_method):
    """Create charge with idempotency key derived from order_id"""

    # Use order_id to generate stable idempotency key
    idempotency_key = f"order_{order_id}"

    charge = stripe.Charge.create(
        amount=amount,
        currency=currency,
        source=payment_method,
        idempotency_key=idempotency_key,
        metadata={"order_id": order_id}
    )

    return charge

# If called twice with same order_id, returns same charge (no duplicate)
charge1 = create_charge_idempotent("order_12345", 5000, "usd", "tok_visa")
charge2 = create_charge_idempotent("order_12345", 5000, "usd", "tok_visa")

assert charge1.id == charge2.id  # Same charge!
```

---

## Test Cards & Scenarios

### Basic Test Cards

| Card Number        | Scenario           | Result                  |
| ------------------ | ------------------ | ----------------------- |
| `4242424242424242` | Basic card         | Always succeeds         |
| `4000002500003010` | 3DS required       | Requires authentication |
| `4000000000009995` | Insufficient funds | Always declines         |
| `4000000000000002` | Generic decline    | Card declined           |
| `5555555555554444` | Mastercard         | Always succeeds         |
| `378282246310005`  | Amex               | Always succeeds         |
| `6011111111111117` | Discover           | Always succeeds         |

### Testing 3DS (SCA) Flow

```python
import stripe

# Use 3DS-required test card
intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    payment_method_data={
        "type": "card",
        "card": {
            "number": "4000002500003010",  # Requires 3DS
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123"
        }
    },
    confirm=True,
    return_url="https://mystore.com/checkout/success"
)

# Status will be 'requires_action' (3DS needed)
print(f"Status: {intent.status}")  # requires_action

# Frontend would handle the client_secret and complete 3DS
```

### Testing Dispute Scenarios

```python
# Use card that triggers disputes
charge = stripe.Charge.create(
    amount=5000,
    currency="usd",
    source="tok_chargeCustomerFail"  # Simulates customer dispute
)

# Later, you'd receive charge.dispute.created webhook
```

### Testing Rate Limits

```python
# Stripe will return rate_limit_error after ~100 requests/second
# Use exponential backoff pattern (shown earlier)
```

---

## TAM Debugging Checklist

### When a merchant says "payments aren't working"

**Step 1: Ask the Right Questions**

- [ ] Which API are you using? (Charges vs. PaymentIntents?)
- [ ] What error are you getting? (Show me the exact error message)
- [ ] Is this in test mode or live?
- [ ] Which payment method? (Card, bank account, wallet?)
- [ ] Is this one customer or all customers?
- [ ] How many transactions are failing?

**Step 2: Check Stripe's System Status**

- [ ] Visit https://status.stripe.com (is there an incident?)

**Step 3: Review Error Code**

- [ ] Is it TEMPORARY (retry), PERMANENT (customer action), or ACTION_REQUIRED (3DS)?
- [ ] Cross-reference against Stripe docs for that error code

**Step 4: Gather Data**

- [ ] Get the Charge ID or PaymentIntent ID
- [ ] Retrieve the object: `stripe.Charge.retrieve("ch_...")`
- [ ] Check status, failure_reason, error_code
- [ ] Check webhooks: were they sent? Received? 200 OK returned?

**Step 5: Identify Root Cause**

- [ ] Is it Stripe? (Check API response codes)
- [ ] Is it the merchant's code? (Missing fields, wrong format)
- [ ] Is it the payment method? (Card declined, expired)
- [ ] Is it the bank/network? (Card network reject, acquirer timeout)

**Step 6: Recommend Solution**

- [ ] If Stripe issue → escalate to support, provide logs
- [ ] If code issue → explain fix, provide code example
- [ ] If card issue → customer needs different card
- [ ] If bank issue → explain hold/timing, no immediate fix

**Step 7: Enable Their Team**

- [ ] Teach them to debug themselves next time
- [ ] Point to relevant docs section
- [ ] Provide a script or webhook pattern they can copy
- [ ] Schedule follow-up to confirm it's working

### Common Scenarios

**Scenario: "Charge succeeded in Stripe Dashboard but customer didn't receive confirmation"**

- [ ] Check if webhook listener is running
- [ ] Check webhook logs in Dashboard (Developers > Webhooks)
- [ ] Was `charge.succeeded` event sent?
- [ ] Did merchant's endpoint return 200 OK?
- [ ] Is merchant's code actually processing the webhook?

**Scenario: "Stripe says payment succeeded but our system shows it as pending"**

- [ ] Check `charge.status` (should be `succeeded`)
- [ ] Check if merchant's code has a bug (maybe not updating DB correctly)
- [ ] Check if webhook was processed (maybe out of order)

**Scenario: "I don't see the charge in my Stripe Dashboard but API returned success"**

- [ ] Did API actually return `succeeded` or `processing`?
- [ ] If `processing`, charge is pending (check back in a few minutes)
- [ ] Is this test mode or live? (Different dashboards)
- [ ] Are you looking at the right account? (Did you switch accounts?)

**Scenario: "3DS authentication shows but customer completes it and charge still fails"**

- [ ] Is the 3DS result being sent back to Stripe?
- [ ] Is the PaymentIntent being confirmed with the 3DS result?
- [ ] Check PaymentIntent status (should move to `succeeded` after successful auth)

---

## Quick Reference: When to Use What

### Use PaymentIntents When:

- ✅ Building new integration (recommended)
- ✅ Charging customers in EU (PSD2/SCA required)
- ✅ You need 3DS support
- ✅ You want Stripe to handle complexity automatically

### Use Charges API When:

- ⚠️ Legacy code you're maintaining (don't use for new features)
- ⚠️ Simple payments, no 3DS needed, non-EU (but still migrate eventually)

### Use Subscriptions When:

- ✅ Recurring charges (monthly, yearly)
- ✅ SaaS pricing
- ✅ You want Stripe to handle retry logic and dunning

### Use Webhooks When:

- ✅ You need to react to Stripe events asynchronously
- ✅ Fulfillment, notifications, reporting
- ✅ You don't want to poll the API constantly

### Use Radar When:

- ✅ You want fraud detection
- ✅ You want to customize block/auth rules
- ✅ You have disputes you want to prevent

### Use Connect When:

- ✅ You're building a marketplace
- ✅ Multiple vendors need to receive payouts
- ✅ You want Stripe to handle seller compliance

---

## TAM Communication Templates

### "Our fraud rate is too high"

> You're probably seeing high decline rates (which is good—fraud blocked) or high chargeback rates (which is bad—fraud got through). Let's clarify: Are customers complaining about legitimate purchases being declined? Or are you seeing chargebacks? That determines the fix. If false positives, we can adjust Radar rules. If chargebacks, we need to look at evidence submission processes.

### "We're losing customers to payment failures"

> Let me pull your decline breakdown. We'll look at: how many are permanent (card_declined) vs. temporary (rate_limit), by card type, by geography. Then I'll recommend specific fixes—could be smarter retry logic, could be showing customers a better error message, could be requiring 3DS only for higher-risk cards.

### "We need to scale payments to 10x volume"

> Great! Let's talk about: your current charge volume, which APIs you're using, whether you've implemented idempotency keys and retry logic, your webhook architecture. We'll review for bottlenecks. Most likely, we'll move you from serial processing to async/queue-based, ensure you're not polling the API, and test rate limits with the staging environment.

### "We have a PSD2 deadline and haven't implemented 3DS"

> The good news is Stripe handles 3DS automatically with PaymentIntents. You don't need to build a separate 3DS flow. Here's the migration path: switch from Charges to PaymentIntents, confirm payment, check if `status == 'requires_action'`, and pass the `client_secret` to your frontend for 3DS handling. Should take 2 weeks for most integrations.

---

## Final Notes

**Remember: You're not a helpdesk, you're a consultant.**

- Don't just send links, explain the concept
- Don't just say "you're doing it wrong," show how to do it right
- Don't dismiss their problem, find the root cause
- Don't make them feel bad about missing features, educate them on best practices

**Your goal:** Leave every interaction with a merchant thinking "that TAM understands our business and cares about our success."

Good luck. Now go impress Stripe. 🚀
