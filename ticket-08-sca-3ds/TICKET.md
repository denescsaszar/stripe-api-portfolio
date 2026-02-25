# Ticket 08 — SCA / 3D Secure for PSD2 Compliance

**Account:** TechnoShop GmbH (Berlin)
**Plan:** Stripe Advanced
**Reported by:** Compliance Officer, Petra Müller
**Priority:** Critical

---

## What the merchant reported

> "We just received a legal notice: PSD2 (Payment Services Directive 2) requires Strong Customer
> Authentication for all card payments in Europe by the end of this month. We have no idea what
> this means for our integration or how Stripe handles it. Our entire checkout is at risk of
> breaking if we don't comply. We need help NOW."

---

## What we know

- TechnoShop is a Berlin-based e-commerce platform selling consumer electronics
- They accept card payments from customers across the EU
- Their current integration uses a simple PaymentIntent flow with Stripe.js
- They have zero 3D Secure / SCA implementation
- PSD2 compliance deadline is in 3 weeks
- If they're not compliant, card payments will be declined

---

## Your task as TAM

1. Explain what PSD2 and SCA actually mean (not legal jargon — technical)
2. Show how Stripe handles SCA automatically with PaymentIntents
3. Build a code example showing `requires_action` flow (3D Secure challenge)
4. Demonstrate how to handle the `payment_intent.payment_action_required` webhook
5. Show the customer-side challenge experience (redirect + return)
6. Provide a compliance checklist

---

## Stripe concepts involved

- PSD2 and Strong Customer Authentication (SCA)
- 3D Secure (3DS) as the authentication method
- PaymentIntent status: `requires_action` when 3DS is needed
- `client_secret` for frontend challenge retrieval
- `stripe.confirmCardPayment()` with `redirect: 'if_required'`
- Webhooks: `payment_intent.payment_action_required`, `payment_intent.succeeded`
- Test cards that trigger 3DS (e.g., 4000 0025 0000 3010)

---

## Expected output

A guide showing:

- How to detect when 3DS is required
- How to present the 3DS challenge to the customer
- How to handle the webhook after authentication
- Test results showing both succeeded and failed 3DS flows

## Output

![PSD2 Compliance Guide - Part 1](./assets/psd2-guide-part1.png)
![PSD2 Compliance Guide - Part 2](./assets/psd2-guide-part2.png)
![PSD2 Compliance Guide - Part 3](./assets/psd2-guide-part3.png)
![PSD2 Compliance Guide - Part 4](./assets/psd2-guide-part4.png)
![PSD2 Compliance Guide - Part 5](./assets/psd2-guide-part5.png)
