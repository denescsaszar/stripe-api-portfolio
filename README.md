# stripe-api-portfolio

A hands-on lab of 20 real-world Stripe scenarios — each modelled as an inbound TAM ticket, diagnosed, and resolved in Python.

Built to go beyond documentation. Every scenario here reflects the kind of problem a TAM encounters in a Gold Standard support engagement: a merchant is losing revenue, a platform is broken, a deadline is real.

---

## Why this exists

Stripe TAMs sit at the intersection of technical depth and user trust. This portfolio is my way of proving I can operate there — not just explain Stripe's products, but debug them, script around them, and help a merchant move forward.

---

## Coverage

| #   | Scenario                                               | Stripe Surface                |
| --- | ------------------------------------------------------ | ----------------------------- |
| 01  | Payment decline investigation                          | Payments, decline codes       |
| 02  | Webhook event verification & failure recovery          | Webhooks, event objects       |
| 03  | Dispute evidence submission automation                 | Disputes, Evidence API        |
| 04  | Custom Radar rules for fraud prevention                | Radar, risk evaluation        |
| 05  | Connect platform — connected account onboarding        | Connect, requirements         |
| 06  | Subscription invoice failure & smart retry             | Billing, invoice lifecycle    |
| 07  | Payout delay root-cause investigation                  | Payouts, balance transactions |
| 08  | SCA / 3D Secure for PSD2 compliance                    | PaymentIntents, 3DS           |
| 09  | Multi-currency payment setup (EUR, GBP, PLN)           | Payments, currency handling   |
| 10  | Sigma SQL — decline pattern analysis                   | Stripe Sigma, SQL             |
| 11  | Idempotency keys — preventing duplicate charges        | Payments, API reliability     |
| 12  | Bulk refund processing for a product recall            | Refunds, automation           |
| 13  | Payment Links for a non-technical merchant             | Payment Links, no-code        |
| 14  | API rate limit handling with exponential backoff       | API, error handling           |
| 15  | Webhook signature verification                         | Security, webhooks            |
| 16  | Billing portal — customer self-service setup           | Customer Portal, Billing      |
| 17  | Radar rule testing & simulation                        | Radar, test mode              |
| 18  | Charge metadata — organising custom fields at scale    | Metadata, reporting           |
| 19  | Balance reconciliation — payouts vs. internal ledger   | Payouts, reconciliation       |
| 20  | Local development with Stripe CLI & webhook forwarding | Stripe CLI, dev tooling       |

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
