# Ticket 09: Multi-currency Payment Setup

## Merchant Profile

**Company:** GlobeShop Ltd  
**Location:** London, UK  
**Business:** Fashion e-commerce, expanding to EU and Asia  
**Problem:** Customers in 15+ countries want to pay in their local currency. Currently only accept GBP and USD. Need to expand payment options without overwhelming complexity.

## Challenge

- How to handle currency conversion and exchange rates
- Which currencies to support and why
- How to optimize for conversion rates vs. fees
- Handling refunds across currencies
- Reporting and reconciliation across multiple currencies

## What a TAM Would Explain

1. Stripe supports 135+ currencies
2. How to handle currency selection (auto-detect, customer choice, etc.)
3. Exchange rate management (Stripe rates vs. fixed rates)
4. Settlement currencies (how/when funds are converted)
5. Pricing impact (Stripe takes slightly lower fee for some currency pairs)

## Your Task

Build a solution that shows:

- How to create PaymentIntents in multiple currencies
- Exchange rate handling
- How to set up multi-currency accounts
- Example flow for EU expansion

![Multi-currency Charges Demo](assets/ticket-09-charges-demo.png)
![Exchange Rates & Fees](assets/ticket-09-exchange-rates.png)
![Balance & Settlement](assets/ticket-09-balance-settlement.png)
![TAM Summary](assets/ticket-09-summary.png)
