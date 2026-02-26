# Stripe Webhooks Bible — Complete Reference

Everything a TAM needs to know about Stripe webhooks: setup, verification, event types, retry logic, and production patterns.

---

## Part 1: How Webhooks Work

```
1. Something happens in Stripe (payment succeeds, dispute created, etc.)
2. Stripe creates an Event object
3. Stripe sends HTTP POST to your endpoint URL
4. Your server processes the event and returns 200 OK
5. If your server fails (non-2xx), Stripe retries for up to 72 hours
```

### Why Webhooks Matter

- **Asynchronous events:** 3DS authentication, SEPA payments, disputes can take hours/days
- **Server-side confirmation:** Don't trust the client — webhook = Stripe confirming what happened
- **Automation:** Auto-fulfill orders, send emails, update databases
- **Without webhooks:** You'd have to poll the API constantly (wasteful, unreliable)

---

## Part 2: Setting Up Webhooks

### In Dashboard

```
Dashboard -> Developers -> Webhooks -> Add endpoint
URL: https://yourdomain.com/webhooks/stripe
Events: Select which events to receive
```

### Via API

```python
webhook_endpoint = stripe.WebhookEndpoint.create(
    url="https://yourdomain.com/webhooks/stripe",
    enabled_events=[
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "invoice.payment_failed",
        "customer.subscription.deleted",
    ],
)
# Save webhook_endpoint.secret for signature verification
```

### Via Stripe CLI (Local Development)

```bash
# Forward events to local server
stripe listen --forward-to localhost:5000/webhooks/stripe

# You'll get a webhook signing secret: whsec_...
# Use this for local signature verification

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger invoice.payment_failed
```

---

## Part 3: Signature Verification (CRITICAL)

**Never process a webhook without verifying the signature.** Without it, anyone can POST fake events to your endpoint.

### Python (Flask)

```python
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)
endpoint_secret = "whsec_abc123..."  # From Dashboard or CLI

@app.route("/webhooks/stripe", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature — possible attack
        return jsonify({"error": "Invalid signature"}), 400

    # Event is verified — safe to process
    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        print(f"Payment succeeded: {pi['id']} for {pi['amount']}")
        # Fulfill the order here

    elif event["type"] == "payment_intent.payment_failed":
        pi = event["data"]["object"]
        print(f"Payment failed: {pi['id']}")
        # Notify the customer

    # Return 200 quickly — process async if needed
    return jsonify({"status": "ok"}), 200
```

### Key Rules for Signature Verification

1. Use the **raw request body** (not parsed JSON) for verification
2. The signing secret is **per-endpoint** — each webhook endpoint has its own
3. Signatures expire after **5 minutes** (tolerance is configurable)
4. **Never skip verification** — even in test mode

---

## Part 4: Event Object Structure

```json
{
  "id": "evt_1234abc",
  "object": "event",
  "api_version": "2024-06-20",
  "created": 1700000000,
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_xyz",
      "object": "payment_intent",
      "amount": 34900,
      "currency": "eur",
      "status": "succeeded",
      "metadata": {
        "order_id": "NB-12345"
      }
    },
    "previous_attributes": {
      "status": "processing"
    }
  },
  "livemode": false,
  "pending_webhooks": 1,
  "request": {
    "id": "req_abc",
    "idempotency_key": null
  }
}
```

| Field | What it means |
|-------|--------------|
| `id` | Unique event ID |
| `type` | Event type (e.g., `payment_intent.succeeded`) |
| `data.object` | The actual Stripe object that changed |
| `data.previous_attributes` | What changed (only the fields that differ) |
| `created` | Unix timestamp of when event occurred |
| `livemode` | true = production, false = test mode |
| `pending_webhooks` | Number of endpoints still to be notified |

---

## Part 5: Essential Event Types

### Payments

| Event | When it fires | What to do |
|-------|--------------|------------|
| `payment_intent.created` | PI created | Usually ignore |
| `payment_intent.succeeded` | Payment completed | Fulfill order |
| `payment_intent.payment_failed` | Payment failed | Notify customer, log reason |
| `payment_intent.requires_action` | 3DS needed | Send customer to auth page |
| `payment_intent.canceled` | PI canceled | Update order status |
| `charge.succeeded` | Charge completed | Secondary confirmation |
| `charge.failed` | Charge failed | Log failure reason |
| `charge.refunded` | Refund processed | Update order, notify customer |
| `charge.dispute.created` | Chargeback opened | Alert team, prepare evidence |
| `charge.dispute.closed` | Dispute resolved | Update records |

### Billing / Subscriptions

| Event | When it fires | What to do |
|-------|--------------|------------|
| `invoice.created` | New invoice generated | Review before payment |
| `invoice.paid` | Invoice paid successfully | Confirm subscription active |
| `invoice.payment_failed` | Invoice payment failed | Retry or notify customer |
| `invoice.payment_action_required` | 3DS needed for invoice | Email customer auth link |
| `invoice.upcoming` | Invoice coming in ~3 days | Preview, adjust if needed |
| `customer.subscription.created` | New subscription | Provision access |
| `customer.subscription.updated` | Sub changed (plan, status) | Update access level |
| `customer.subscription.deleted` | Sub canceled | Revoke access |
| `customer.subscription.trial_will_end` | Trial ending in 3 days | Notify customer |

### Connect

| Event | When it fires | What to do |
|-------|--------------|------------|
| `account.updated` | Connected account changed | Check requirements |
| `account.application.authorized` | User authorized your app | Create account record |
| `account.application.deauthorized` | User removed your app | Clean up |
| `payout.created` | Payout initiated | Log for reconciliation |
| `payout.paid` | Payout arrived at bank | Confirm delivery |
| `payout.failed` | Payout failed | Investigate bank issue |

### Disputes

| Event | When it fires | What to do |
|-------|--------------|------------|
| `charge.dispute.created` | New dispute/chargeback | Start evidence collection |
| `charge.dispute.updated` | Evidence submitted or status change | Track progress |
| `charge.dispute.closed` | Dispute resolved (won/lost) | Update records |
| `charge.dispute.funds_withdrawn` | Funds debited for dispute | Accounting update |
| `charge.dispute.funds_reinstated` | Dispute won, funds returned | Accounting update |

### Radar

| Event | When it fires | What to do |
|-------|--------------|------------|
| `radar.early_fraud_warning.created` | Visa/MC fraud alert | Review charge, consider refund |
| `radar.early_fraud_warning.updated` | Warning updated | Reassess |

---

## Part 6: Retry Logic

### Stripe's Retry Schedule

When your endpoint returns non-2xx or times out, Stripe retries:

```
Attempt 1: Immediately
Attempt 2: ~1 hour later
Attempt 3: ~2 hours later
Attempt 4: ~4 hours later
Attempt 5: ~8 hours later
... continues with exponential backoff
Total retry window: 72 hours
```

After 72 hours of failures, Stripe **disables the endpoint** and emails you.

### What Counts as Success/Failure

| Response | Stripe's interpretation |
|----------|------------------------|
| 200-299 | Success — event delivered |
| 300-399 | Failure — redirects not followed |
| 400-499 | Failure — will retry |
| 500-599 | Failure — will retry |
| Timeout (>20s) | Failure — will retry |
| Connection refused | Failure — will retry |

### Best Practice: Respond Fast, Process Async

```python
@app.route("/webhooks/stripe", methods=["POST"])
def webhook():
    # Verify signature (fast)
    event = stripe.Webhook.construct_event(payload, sig, secret)

    # Queue for async processing (fast)
    queue.enqueue(process_event, event)

    # Return 200 immediately (under 1 second)
    return "", 200

def process_event(event):
    # Heavy processing happens here (async)
    if event["type"] == "payment_intent.succeeded":
        fulfill_order(event["data"]["object"])
        send_confirmation_email(event["data"]["object"])
```

---

## Part 7: Handling Duplicate Events

Stripe may send the same event multiple times. Your handler must be **idempotent**.

```python
# Track processed events in your database
processed_events = set()  # In production: use a database table

@app.route("/webhooks/stripe", methods=["POST"])
def webhook():
    event = stripe.Webhook.construct_event(payload, sig, secret)

    # Skip if already processed
    if event["id"] in processed_events:
        return "", 200

    # Process the event
    handle_event(event)

    # Mark as processed
    processed_events.add(event["id"])
    return "", 200
```

### Why Duplicates Happen

- Network timeout: your server processed it but Stripe didn't get the 200
- Stripe internal retry: rare but possible
- Endpoint temporarily down then back up

---

## Part 8: Recovering Missed Events

### Replay Specific Events (CLI)

```bash
# Resend a specific event
stripe events resend evt_1234abc

# Resend to a specific endpoint
stripe events resend evt_1234abc --webhook-endpoint we_xyz
```

### Query Events API

```python
# Get all events from the last 24 hours
import time

events = stripe.Event.list(
    created={"gte": int(time.time()) - 86400},
    limit=100,
    type="payment_intent.succeeded"
)

for event in events.auto_paging_iter():
    print(f"{event.id}: {event.type} at {event.created}")
```

### Key Limits

| Limit | Value |
|-------|-------|
| Event storage | 30 days |
| Retry window | 72 hours |
| Webhook timeout | 20 seconds |
| Max endpoints per account | 16 (can request more) |
| Events per second | Thousands (no practical limit) |

---

## Part 9: Event Ordering

**Events are NOT guaranteed to arrive in order.** Your code must handle this.

```
Possible order you receive:
1. payment_intent.succeeded  (created at 10:00:01)
2. payment_intent.created    (created at 10:00:00)  <- arrived late!
```

### How to Handle

```python
def handle_event(event):
    obj = event["data"]["object"]

    # Always check the current object state, not the event
    if event["type"] == "payment_intent.succeeded":
        # Verify by fetching the latest state
        pi = stripe.PaymentIntent.retrieve(obj["id"])
        if pi.status == "succeeded":
            fulfill_order(pi)
        # else: status already changed again, skip
```

**Rule:** Use the event as a trigger, but always fetch the latest object state before acting.

---

## Part 10: Webhook Debugging Checklist

When a merchant says "our webhooks aren't working":

| Check | How | Common Issue |
|-------|-----|-------------|
| Endpoint URL correct? | Dashboard -> Webhooks | Typo, wrong environment |
| Endpoint returning 200? | Check webhook logs in Dashboard | Server error (500) |
| Signature verification working? | Check for `SignatureVerificationError` | Wrong signing secret |
| Using raw body for verification? | Check code | Parsing JSON before verify |
| Endpoint reachable? | `curl -X POST <url>` | Firewall, DNS, SSL issue |
| Correct events selected? | Dashboard -> Webhook -> Events | Missing event subscription |
| Test vs live mode? | Check key prefix | Using test key for live events |
| Processing fast enough? | Check for timeouts | Heavy sync processing |

### Dashboard Webhook Logs

```
Dashboard -> Developers -> Webhooks -> Select endpoint -> Attempts
```

Shows: every event sent, response code, response time, retry schedule.

---

## Part 11: Production Webhook Architecture

### Minimal (Start Here)

```
Stripe -> Your Server (Flask/Express) -> Process inline -> Return 200
```

### Recommended (Production)

```
Stripe -> Your Server -> Verify signature -> Push to queue -> Return 200
                                                    |
                                              Queue Worker -> Process event
                                                    |
                                              Database -> Track processed events
```

### Enterprise

```
Stripe -> Load Balancer -> Multiple webhook receivers -> Message queue (SQS/Redis)
                                                              |
                                                    Worker fleet -> Process events
                                                              |
                                                    Dead letter queue -> Failed events
                                                              |
                                                    Alerting -> PagerDuty/Slack
```

---

*Webhooks are the nervous system of a Stripe integration. If they're not working, the merchant is blind to what's happening with their payments.*
