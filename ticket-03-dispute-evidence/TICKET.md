# Ticket 03 — Dispute Evidence Submission

**Account:** Velora Fashion (Munich)
**Plan:** Stripe Advanced
**Reported by:** Head of Finance, Sophie Brenner
**Priority:** High

---

## What the merchant reported

> "We've just received 12 chargebacks this week — all from customers claiming
> they never received their orders. We know these are fraudulent disputes, we
> have shipping confirmations and delivery tracking for every single one.
> But we have no idea how to fight them through Stripe. We've never submitted
> dispute evidence before and we're worried about missing the deadlines."

---

## What we know

- Merchant sells fashion online, ships across DE, AT, CH via DHL
- All 12 disputes are reason code: `product_not_received`
- They have tracking numbers, delivery confirmations, and customer emails
- Stripe dispute deadline: 7–21 days depending on card network
- Merchant has never submitted evidence through Stripe before

---

## Your task as TAM

1. Explain how the dispute lifecycle works in Stripe
2. Show how to retrieve all open disputes via the API
3. Demonstrate submitting evidence programmatically using the Disputes API
4. Explain what evidence matters most for `product_not_received` disputes
5. Show how to check dispute status and deadlines

---

## Stripe concepts involved

- `Dispute` object and its `evidence` sub-object
- Dispute reason codes: `product_not_received`, `fraudulent`, `duplicate`
- `stripe.Dispute.modify()` to submit evidence
- Evidence fields: `shipping_tracking_number`, `customer_email_address`,
  `shipping_documentation`, `customer_signature`
- Dispute deadlines — varies by card network (Visa: 20 days, Mastercard: 45 days)
- Dispute status: `needs_response`, `under_review`, `won`, `lost`

---

## Expected output

- A script that lists all open disputes with deadlines
- A working evidence submission using the Stripe API
- Clear guidance on what evidence wins `product_not_received` cases
