# Ticket 07 — Payout Delay Root-Cause Investigation

**Account:** SwiftShop GmbH (Munich)
**Plan:** Stripe Advanced
**Reported by:** Finance Lead, Thomas Schmidt
**Priority:** High

---

## What the merchant reported

> "Our payouts have been delayed for the last 3 days. We normally receive payouts daily
> at 9 AM Munich time, but since Monday nothing has arrived. We have €47,000 in pending
> balance and no visibility into why the payouts aren't going out. Is it a Stripe issue,
> a bank issue, or something wrong with our account?"

---

## What we know

- SwiftShop is a mid-market e-commerce platform (Germany, Austria, Switzerland)
- They accept payments daily, volume ~€15,000-20,000/day
- Automatic payouts enabled: daily, minimum €1,000, to their German bank account
- No recent integration changes reported
- Last successful payout: March 19 at 9:02 AM
- Current balance: €47,230 (well above minimum threshold)

---

## Your task as TAM

1. Investigate the payout schedule and identify why payouts have stopped
2. Check for account holds, restrictions, or verification issues blocking payouts
3. Query the Payout API to see the status of recent payout attempts
4. Investigate balance transactions to understand where the money is
5. Identify whether the issue is Stripe-side, bank-side, or account configuration

---

## Stripe concepts involved

- Payout objects and their statuses (`pending`, `paid`, `failed`, `canceled`)
- Payout schedule configuration (automatic vs. manual)
- Account holds and payout restrictions (`requirements.currently_due`)
- Balance transactions and how they relate to payouts
- Bank transfer failures and retry logic
- Balance object and available vs. pending balance
- Payout method configuration and bank account verification

---

## Expected output

A diagnostic report showing:

- Last 10 payout attempts and their status
- Account holds or restrictions blocking payouts
- Current balance breakdown (available, pending, reserved)
- Bank account verification status
- Timeline of when payouts stopped and why
- Recommended next steps for the merchant

---

## Output

### Account & Payout Status

![Payout Status](assets/payout-status.png)

### Root-Cause Analysis

![Root-Cause Analysis](assets/root-cause-analysis.png)
