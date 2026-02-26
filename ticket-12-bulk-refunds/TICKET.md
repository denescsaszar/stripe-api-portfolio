# Ticket 12 — Bulk Refund Processing for a Product Recall

**Account:** NordBrew (Copenhagen)  
**Plan:** Stripe Scale  
**Reported by:** COO, Erik Lindqvist  
**Priority:** Critical

---

## What the merchant reported

> "We're a specialty coffee equipment company that sells across Europe. Last week we
> discovered a safety defect in our flagship espresso machine — the NordBrew Pro 3000.
> We've sold 147 units in the last 60 days at €349 each and need to issue a full refund
> to every customer immediately. Our legal team says we have 48 hours to process all
> refunds before we issue the public recall notice. Can you help us do this in bulk?
> We can't afford to click through 147 refunds manually in the Dashboard."

---

## What we know

- Merchant sells premium coffee equipment (€150–€600 range)
- Product recall: NordBrew Pro 3000 espresso machine (€349)
- 147 units sold in last 60 days, all need full refunds
- Volume: ~2,000 payments/month across all products
- Stack: Python backend, PaymentIntents API
- Current approach: Manual refunds via Dashboard (too slow for 147)
- Legal deadline: 48 hours for all refunds to be initiated
- Some payments may have been partially refunded already (warranty claims)
- Need: Audit trail for legal compliance

---

## Your task as TAM

1. Search PaymentIntents for all NordBrew Pro 3000 purchases in the last 60 days
2. Filter for refund-eligible payments (succeeded, not already fully refunded)
3. Process refunds in bulk with error handling for edge cases
4. Handle partial refunds (some customers already received warranty refunds)
5. Generate a compliance report with full audit trail
6. Demonstrate dry-run mode (preview before executing)

---

## Stripe concepts involved

- Refund API: full and partial refunds via PaymentIntent
- PaymentIntent search: filtering by metadata, amount, date range
- Refund idempotency: preventing duplicate refunds
- Charge object: checking existing refund amounts
- Error handling: already_refunded, charge_expired, insufficient balance
- Metadata: tagging refunds with recall reference numbers

---

## Expected output

A working demonstration showing:

- Discovery of all eligible payments for the recalled product
- Dry-run preview showing exactly what will be refunded
- Bulk refund execution with per-payment error handling
- Handling of edge cases (already refunded, partial refunds)
- Compliance report with timestamps and refund IDs
- Summary statistics (total refunded, skipped, failed)

---

## Solution Output

### Payment Discovery & Eligibility Check

![Payment Discovery](ticket-12-payment-discovery.png)
_Searching for NordBrew Pro 3000 purchases and checking refund eligibility_

### Dry Run Preview

![Dry Run](ticket-12-dry-run.png)
_Preview of all refunds before execution — no money moves yet_

### Bulk Refund Execution

![Bulk Execution](ticket-12-bulk-execution.png)
_Processing refunds with real-time progress and error handling_

### Compliance Report

![Compliance Report](ticket-12-compliance-report.png)
_Full audit trail for legal documentation_
