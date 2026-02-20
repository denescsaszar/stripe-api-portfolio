# Ticket 01 — Payment Decline Investigation

**Account:** TechGear GmbH (Berlin)
**Plan:** Stripe Advanced
**Reported by:** Head of Payments, Anna Müller
**Priority:** High

---

## What the merchant reported

> "Hi, we are seeing a sharp increase in failed payments over the last 48 hours.
> Roughly 30% of our checkout attempts are not going through. We have not changed
> anything on our end. Our peak sales season starts Friday and this is critical.
> Please help urgently."

---

## What we know

- Merchant is a B2C e-commerce platform selling consumer electronics across DE, AT, CH
- They use Stripe Elements for checkout with a standard PaymentIntent flow
- Average transaction value: €180
- Volume: ~2,000 payment attempts per day
- No recent integration changes reported by their engineering team

---

## Your task as TAM

1. Pull their recent failed PaymentIntents from the Stripe API
2. Group failures by decline code to identify the dominant failure reason
3. Identify whether this is a card-issuer problem, a fraud block, or an integration issue
4. Prepare a clear diagnosis and recommended next steps for Anna

---

## Stripe concepts involved

- `PaymentIntent` object and its `last_payment_error` field
- Decline codes: `insufficient_funds`, `do_not_honor`, `card_declined`, `incorrect_cvc`
- Difference between issuer declines vs. Stripe/Radar blocks
- `status: requires_payment_method` as the end state of a failed PaymentIntent

---

## Expected output

A diagnostic summary showing:

- Total attempts vs. failures
- Breakdown by decline code
- Clear recommendation the merchant can act on today
