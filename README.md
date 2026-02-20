# stripe-api-portfolio

A hands-on lab of 20 real-world Stripe scenarios — each modelled as an inbound TAM ticket, diagnosed, and resolved in Python.

Built to go beyond documentation. Every scenario here reflects the kind of problem a TAM encounters in a Gold Standard support engagement: a merchant is losing revenue, a platform is broken, a deadline is real.

---

## Why this exists

Stripe TAMs sit at the intersection of technical depth and user trust. This portfolio is my way of proving I can operate there — not just explain Stripe's products, but debug them, script around them, and help a merchant move forward.

---

## Coverage

| #   | Scenario                                               | Stripe Surface                | Status |
| --- | ------------------------------------------------------ | ----------------------------- | ------ |
| 01  | Payment decline investigation                          | Payments, decline codes       | ✅     |
| 02  | Webhook event verification & failure recovery          | Webhooks, event objects       | ✅     |
| 03  | Dispute evidence submission automation                 | Disputes, Evidence API        |        |
| 04  | Custom Radar rules for fraud prevention                | Radar, risk evaluation        |        |
| 05  | Connect platform — connected account onboarding        | Connect, requirements         |        |
| 06  | Subscription invoice failure & smart retry             | Billing, invoice lifecycle    |        |
| 07  | Payout delay root-cause investigation                  | Payouts, balance transactions |        |
| 08  | SCA / 3D Secure for PSD2 compliance                    | PaymentIntents, 3DS           |        |
| 09  | Multi-currency payment setup (EUR, GBP, PLN)           | Payments, currency handling   |        |
| 10  | Sigma SQL — decline pattern analysis                   | Stripe Sigma, SQL             |        |
| 11  | Idempotency keys — preventing duplicate charges        | Payments, API reliability     |        |
| 12  | Bulk refund processing for a product recall            | Refunds, automation           |        |
| 13  | Payment Links for a non-technical merchant             | Payment Links, no-code        |        |
| 14  | API rate limit handling with exponential backoff       | API, error handling           |        |
| 15  | Webhook signature verification                         | Security, webhooks            |        |
| 16  | Billing portal — customer self-service setup           | Customer Portal, Billing      |        |
| 17  | Radar rule testing & simulation                        | Radar, test mode              |        |
| 18  | Charge metadata — organising custom fields at scale    | Metadata, reporting           |        |
| 19  | Balance reconciliation — payouts vs. internal ledger   | Payouts, reconciliation       |        |
| 20  | Local development with Stripe CLI & webhook forwarding | Stripe CLI, dev tooling       |        |

---

## Stack

Python 3.11 · Stripe SDK · Flask · SQL (Stripe Sigma) · Stripe CLI · Postman

---

## Structure

Each ticket folder contains:

- `TICKET.md` — the scenario, written as a real merchant-reported issue
- `solution.py` — diagnosis and working resolution in Python

---

## Stripe products covered

Payments · PaymentIntents · Radar · Connect · Billing · Webhooks · Disputes · Payouts · Sigma · Payment Links · Customer Portal · Stripe CLI

---

_Each ticket is self-contained. Start anywhere._

---

## Progress

### Ticket 01 — Payment Decline Investigation

**Account:** TechGear GmbH (Berlin) · **Priority:** High

A merchant reported a 30% spike in failed payments during peak season with no integration changes on their side. Using the Stripe API, we pulled recent PaymentIntents, grouped failures by decline code, and identified the dominant root cause — distinguishing between issuer-side declines (bank blocking the charge) and Stripe/Radar blocks (fraud rules triggering). The output gives the TAM a clear, shareable diagnostic they can send directly to the merchant with a recommended next step.

![Diagnostic Output](ticket-01-payment-decline/assets/diagnostic-output.png)

---

### Ticket 02 — Webhook Debugging & Event Verification

**Account:** Flowbox SaaS (Hamburg) · **Priority:** High

A merchant suspected fake webhook events were being sent to their endpoint — orders were marked paid with no matching charges. They had no signature verification in place. We built a secure Flask webhook receiver using `stripe.Webhook.construct_event()` to cryptographically verify every incoming request, rejecting anything unsigned with HTTP 400. We also queried the Stripe Events API to surface the 11 missed events from the previous 72 hours (visible in the output), demonstrating how to recover from server downtime without losing critical payment data.

![Webhook Output](ticket-02-webhook-debugging/assets/webhook-output.png)
