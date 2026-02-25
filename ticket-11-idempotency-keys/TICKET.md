# Ticket 11 — Idempotency Keys: Preventing Duplicate Charges

**Account:** TravelBook (Amsterdam)  
**Plan:** Stripe Scale  
**Reported by:** CTO, Lotte van den Berg  
**Priority:** Critical

---

## What the merchant reported

> "We're a SaaS platform that books travel packages for agencies across Europe. Last week
> we had a network blip during peak booking season and three customers got charged twice
> for the same trip — €2,400, €1,850, and €3,100. Our support team is drowning in
> refund requests and our agencies are furious. We're using PaymentIntents but clearly
> something is wrong with how we handle retries. Can you help us make sure this never
> happens again?"

---

## What we know

- Merchant is a B2B SaaS platform serving 200+ travel agencies
- Average transaction: €1,200–€3,500 (high-value travel packages)
- Volume: ~8,000 payments/month
- Stack: Python backend, PaymentIntents API
- Current retry logic: simple try/except with immediate retry on timeout
- No idempotency keys in use
- Three confirmed duplicate charges in the last 7 days
- All duplicates occurred during a 15-minute network degradation event

---

## Your task as TAM

1. Demonstrate idempotency key generation strategies (UUID, composite keys)
2. Show how Stripe handles idempotent requests (24-hour window, key reuse)
3. Implement a safe retry strategy with idempotency keys
4. Simulate network failures and prove duplicate protection works
5. Build a key management helper for tracking and auditing idempotency keys
6. Show what happens when you reuse a key vs. use a new one

---

## Stripe concepts involved

- Idempotency keys: ensuring duplicate API requests produce the same result
- Stripe's 24-hour idempotency window
- Key collision handling (same key, different parameters = error)
- PaymentIntent creation with idempotency keys
- Retry strategies: exponential backoff with jitter
- Network timeout handling for payment APIs

---

## Expected output

A working demonstration showing:

- Safe PaymentIntent creation with idempotency keys
- Retry simulation proving no duplicate charges occur
- Key collision detection and error handling
- Comparison: with vs. without idempotency protection
- Audit trail of all idempotency keys used
- Exponential backoff retry implementation

---

## Solution Output

### Idempotency Key Strategy & Safe Payment Creation

![Idempotency Demo](ticket-11-idempotency-demo.png)
_Generating idempotency keys, creating payments with duplicate protection, and verifying single-charge guarantee_

### Retry Simulation & Duplicate Prevention

![Retry Simulation](ticket-11-retry-simulation.png)
_Simulating network failures with automatic retries — proving the same payment is never created twice_

### Key Collision Detection

![Key Collision](ticket-11-key-collision.png)
_Demonstrating what happens when an idempotency key is reused with different parameters_

### Audit Trail & Recommendations

![Audit Trail](ticket-11-audit-trail.png)
_Complete key tracking log and tactical recommendations for TravelBook's production deployment_
