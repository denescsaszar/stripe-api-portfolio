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

A merchant reported a 30% spike in failed payments during peak season with no integration changes on their side. Using the Stripe API, we pulled recent PaymentIntents, grouped failures by decline code, and identified the dominant root cause — distinguishing between issuer-side declines (bank blocking the charge) and Stripe/Radar blocks (fraud rules triggering).

![Diagnostic Output](ticket-01-payment-decline/assets/diagnostic-output.png)

**How a TAM would respond to Anna:**

> "Hi Anna, we've pulled your recent PaymentIntents and identified the pattern. The dominant failure reason is `insufficient_funds` — this is an issuer-side decline, meaning your customers' banks are blocking the charge, not Stripe. There is no integration issue on your side.
>
> For your peak season, I'd recommend three things: first, make sure your checkout shows a clear retry prompt so customers can try a different card. Second, consider offering SEPA Direct Debit as an alternative — it's widely used in DE/AT/CH and bypasses card issuer limits entirely. Third, if you're not already using Stripe's card update emails, enable them so expired or declined cards get updated automatically.
>
> None of these require integration changes — all three can be enabled in your Dashboard today. Want me to walk you through it?"

---

### Ticket 02 — Webhook Debugging & Event Verification

**Account:** Flowbox SaaS (Hamburg) · **Priority:** High

A merchant suspected fake webhook events were being sent to their endpoint — orders were marked paid with no matching charges. They had no signature verification in place. We built a secure Flask webhook receiver using `stripe.Webhook.construct_event()` to cryptographically verify every incoming request, rejecting anything unsigned with HTTP 400. We also queried the Stripe Events API to surface the 11 missed events from the previous 72 hours, demonstrating how to recover from server downtime without losing critical payment data.

![Webhook Output](ticket-02-webhook-debugging/assets/webhook-output.png)

**How a TAM would respond to Lars:**

> "Hi Lars, we've identified two separate issues.
>
> First, the fake events: your endpoint was accepting requests from anyone because webhook signatures weren't being verified. Stripe signs every event with a secret key — without checking that signature, any attacker can POST a fake `payment_intent.succeeded` to your server and trigger order fulfilment for free. The fix is one function call: `stripe.Webhook.construct_event()`. Anything that fails verification gets rejected with HTTP 400 before it touches your database.
>
> Second, the missing events: Stripe retries failed webhooks for up to 72 hours and stores all events for 30 days. We queried the Events API and found the 11 events from that window. You can replay any specific event with `stripe events resend <event_id>` to reprocess orders that were missed.
>
> I've prepared a working implementation you can drop into your stack today. Want to walk through it together on a call?"

---

### Ticket 03 — Dispute Evidence Submission

**Account:** Velora Fashion (Munich) · **Priority:** High

Velora received 12 chargebacks in one week, all with reason code `product_not_received`. They had DHL tracking confirming delivery for every order but had never submitted dispute evidence through Stripe before. We built a script that queries all open disputes via the API, checks deadlines, and submits evidence programmatically using `stripe.Dispute.modify()` — including tracking number, carrier, shipping date, customer email, and a written narrative for the card network. The script saved the evidence as a draft first so the merchant can review in the Dashboard before final submission.

![Dispute Output](ticket-03-dispute-evidence/assets/dispute-output.png)

**How a TAM would respond to Sophie:**

> "Hi Sophie, don't worry — you have the strongest possible evidence for `product_not_received` disputes: confirmed DHL delivery scans. Here's exactly what to do.
>
> For each of the 12 disputes, you need to submit: the DHL tracking number showing delivery confirmed at the customer's address, the customer's email from the order, and a short written summary of the timeline. Stripe forwards this directly to the card network.
>
> The most important thing right now is the deadline — Visa gives you 20 days from the dispute date, Mastercard up to 45. Don't wait. I've prepared a script that pulls all your open disputes, shows the deadlines, and submits the evidence in one run. I can share it with your engineering team today.
>
> One more thing: if you see the same customer name or email appearing across multiple disputes, flag it in your submission — card networks treat repeat disputers differently and it strengthens your case."
