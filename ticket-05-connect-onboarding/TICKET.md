# Ticket 05 — Connect Platform: Connected Account Onboarding

**Account:** Markethub GmbH (Berlin)
**Plan:** Stripe Advanced
**Reported by:** CTO, Fabian Richter
**Priority:** High

---

## What the merchant reported

> "We're building a marketplace where sellers can sign up and receive payouts
> directly. We've integrated Stripe Connect but our sellers are getting stuck
> during onboarding — some complete the form and still show as 'restricted'.
> Others never finish and we don't know why. We're also not sure how to know
> when a seller is fully verified and ready to receive payouts. Can you help
> us understand what's blocking them?"

---

## What we know

- Markethub is a two-sided marketplace — buyers pay, sellers get paid out
- They use Stripe Connect with Express accounts for sellers
- Some connected accounts show `charges_enabled: false` after onboarding
- Others have `payouts_enabled: false` — funds are collected but not paid out
- They are not listening to the `account.updated` webhook event
- They have no visibility into which requirements are blocking each seller

---

## Your task as TAM

1. Explain the Connect account lifecycle and what "restricted" actually means
2. Show how to retrieve a connected account and read its requirements
3. Identify what fields are blocking `charges_enabled` and `payouts_enabled`
4. Show how to use the `account.updated` webhook to track verification progress
5. Explain the difference between Express, Standard, and Custom accounts

---

## Stripe concepts involved

- Connect account types: Express, Standard, Custom
- `charges_enabled` and `payouts_enabled` flags on the Account object
- `requirements.currently_due` — fields blocking activation right now
- `requirements.eventually_due` — fields needed before next threshold
- `requirements.disabled_reason` — why the account is restricted
- `account.updated` webhook — fires when verification status changes
- Onboarding links via `stripe.AccountLink.create()`

---

## Expected output

- A script that lists all connected accounts with their status
- Clear identification of what requirements are blocking each account
- A working onboarding link generator for accounts that need to complete setup

---

## Output

![Onboarding Output](assets/onboarding-output.png)
