# Ticket 10 — Sigma SQL Decline Pattern Analysis

**Account:** PayFlow Analytics (Berlin)  
**Plan:** Stripe Advanced  
**Reported by:** Head of Operations, Marcus Weber  
**Priority:** High

---

## What the merchant reported

> "Hi, our payment decline rate jumped from 1.5% to 3.2% last month and we have no
> idea why. It's costing us thousands in lost revenue. We need to understand: are
> certain card types failing? Geographic regions? Payment amounts? We need data-driven
> insights, not guesses. Can you help us figure this out?"

---

## What we know

- Merchant is a B2B SaaS platform for financial institutions
- Volume: ~50,000 payment attempts per month
- Average transaction value: €450
- No recent integration changes
- Baseline decline rate: 1.5% (industry standard: 1-2%)
- Current decline rate: 3.2% (double the baseline)
- They have Stripe Sigma access but don't know how to use it

---

## Your task as TAM

1. Query Stripe Sigma to analyze all charges from the last 30 days
2. Group declines by: reason code, card brand, customer country, amount range, time of day
3. Identify the dominant failure pattern (e.g., "80% of declines are `insufficient_funds` from Polish cards")
4. Distinguish between issuer-side declines vs. fraud blocks vs. network errors
5. Recommend tactical changes (fraud rules, checkout messaging, customer communication)

---

## Stripe concepts involved

- Stripe Sigma: SQL data warehouse of all your payment data
- Common decline reason codes and their meanings
- Issuer blocks vs. Stripe/Radar blocks vs. network errors
- How to segment declines by geography, card type, amount
- Actionable insights from raw payment data

---

## Expected output

A diagnostic analysis showing:

- Decline breakdown by reason code (with percentages)
- Geographic patterns (which countries have highest decline rate)
- Card brand breakdown
- Correlation with payment amount
- Root cause hypothesis
- Recommended actions for the merchant

---

## Solution Output

### Decline Breakdown Analysis

![Decline Breakdown](ticket-10-decline-breakdown.png)
_Primary decline reason codes, percentages, and classification into issuer blocks vs. fraud blocks vs. network errors_

### Geographic Pattern Analysis

![Geographic Analysis](ticket-10-geographic-analysis.png)
_Decline rates by customer country, highlighting Poland (63% insufficient_funds) as root cause_

### Recommendations & Tactical Actions

![Recommendations](ticket-10-recommendations.png)
_Specific actions to reduce declines: messaging updates, 3DS implementation, retry logic, Polish market optimization_

### Summary & Root Cause

![Summary](ticket-10-summary.png)
_Executive summary of findings: 47% issuer blocks, 24% fraud blocks, 8% network errors, recommended next steps_
