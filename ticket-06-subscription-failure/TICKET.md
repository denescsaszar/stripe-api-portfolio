# Ticket 06 — Subscription Invoice Failure & Smart Retry

**Account:** Audible Books GmbH (Vienna)
**Plan:** Stripe Advanced
**Reported by:** Head of Billing, Maria Fischer
**Priority:** High

---

## What the merchant reported

> "We've had recurring billing issues for the past week. Customers are complaining that they
> can't get their monthly subscriptions set up. When we try to create invoices, payment fails
> silently and we're left with unpaid invoices cluttering our system. We have no visibility
> into why they're failing — is it the card, our integration, or Stripe? Some retries work,
> some don't. We need a way to intelligently retry failed invoices without pestering customers."

---

## What we know

- Audible Books sells monthly audiobook subscriptions (€9.99/month)
- They use Stripe Billing to create invoices automatically
- Failed invoices sit in `draft` state forever — no automatic retry
- ~2-3% of invoices fail on first attempt (normal, mostly temporary card issues)
- Customers don't know their subscription failed — they just notice missing books
- The merchant has no programmatic way to retry intelligently

---

## Your task as TAM

1. Explain why invoice failures are expected and normal
2. Build a script that identifies failed invoices and classifies the failure reason
3. Implement smart retry logic: retry immediately for temporary failures, wait before retrying for others
4. Show how to notify customers of payment failures
5. Demonstrate how to use webhooks to trigger retries automatically

---

## Stripe concepts involved

- Invoice lifecycle: `draft` → `open` → `paid` or `uncollectible`
- Invoice payment failures stored in `last_finalization_error`
- Difference between temporary (`try_again`) and permanent failures (`do_not_honor`)
- Retry strategies: exponential backoff, max retry count
- Webhook events: `invoice.payment_failed`, `invoice.payment_action_required`
- Customer notification via Stripe or custom email

---

## Expected output

A diagnostic script showing:

- Total invoices vs. failed invoices
- Breakdown of failure reasons (card declined, insufficient funds, expired, etc.)
- Retry recommendations per failure type
- A working retry function that implements smart backoff logic

---

## Output

### Diagnostic Breakdown

![Diagnostic Breakdown](assets/diagnostic-breakdown.png)

### Recommendations

![Recommendations](assets/recommendations.png)
