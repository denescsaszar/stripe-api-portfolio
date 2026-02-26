# Stripe Products Bible — Complete Reference

Every Stripe product a TAM needs to know: what it does, who uses it, key features, and how to recommend it.

---

## Part 1: Core Payments

### Payments (PaymentIntents)

**What it is:** Accept one-time payments online.
**Who uses it:** Every Stripe merchant.

| Feature | Detail |
|---------|--------|
| API | PaymentIntents (modern) or Charges (legacy) |
| Flow | Create -> Confirm -> Succeed/Fail |
| 3DS/SCA | Automatic via PaymentIntents |
| Currencies | 135+ |
| Payment methods | Cards, SEPA, iDEAL, Giropay, Klarna, etc. |

**TAM talking points:**
- Always recommend PaymentIntents over legacy Charges API
- `automatic_payment_methods` = Stripe picks best methods for the customer's region
- Auth-and-capture (`capture_method: "manual"`) for merchants who ship before charging

**When a merchant asks:** "How do I accept payments?"
> "Use PaymentIntents with automatic_payment_methods enabled. Stripe will automatically show the right payment methods for each customer's country — cards in the US, SEPA in Germany, iDEAL in Netherlands. One integration, global coverage."

---

### Payment Methods

**What it is:** All the ways customers can pay.

#### Cards

| Feature | Detail |
|---------|--------|
| Brands | Visa, Mastercard, Amex, Discover, JCB, UnionPay, Diners |
| Funding | Credit, debit, prepaid |
| Features | Automatic card updater, network tokens, saved cards |

#### SEPA Direct Debit (DACH critical)

| Feature | Detail |
|---------|--------|
| Markets | EU + EEA (especially DE, AT, NL, BE, FR) |
| Flow | Customer provides IBAN, signs mandate |
| Settlement | 5-14 business days |
| Refund window | 8 weeks (unauthorized: 13 months) |
| Best for | Recurring, subscriptions, high-value |
| Why recommend | No card needed, lower decline rates, lower fees |

#### Giropay (Germany)

| Feature | Detail |
|---------|--------|
| Market | Germany only |
| Flow | Bank redirect, real-time confirmation |
| Best for | E-commerce in DE |
| Note | Being merged with EPS |

#### iDEAL (Netherlands)

| Feature | Detail |
|---------|--------|
| Market | Netherlands |
| Flow | Bank redirect |
| Market share | ~60% of Dutch e-commerce |

#### Klarna (Buy Now Pay Later)

| Feature | Detail |
|---------|--------|
| Markets | EU, US, UK, AU |
| Options | Pay in 4, pay later (30 days), financing |
| Best for | Higher AOV, younger demographics |
| Merchant benefit | Get paid upfront, Klarna takes the risk |

#### SOFORT (Being replaced by SEPA)

| Feature | Detail |
|---------|--------|
| Markets | DE, AT, CH, BE, NL |
| Flow | Bank redirect |
| Status | Being phased out, recommend SEPA instead |

#### Apple Pay / Google Pay

| Feature | Detail |
|---------|--------|
| Setup | Via Payment Request Button (Stripe.js) |
| Benefit | 1-click checkout, higher conversion |
| Works with | PaymentIntents, automatic_payment_methods |

---

### Payment Links

**What it is:** No-code payment page — just a URL.
**Who uses it:** Non-technical merchants, quick invoicing, social media sellers.

| Feature | Detail |
|---------|--------|
| Setup | Dashboard only — zero code |
| Customization | Logo, colors, product details |
| Features | Quantity, tax, shipping, promo codes |
| Sharing | URL, QR code, embed button |
| Recurring | Supports subscriptions |

**TAM talking points:**
- Perfect for merchants who don't have a developer
- Can be created in 60 seconds from the Dashboard
- Supports all payment methods enabled on the account
- Great for invoicing, social media sales, quick prototypes

**When a merchant asks:** "I don't have a website, can I still accept payments?"
> "Yes — use Payment Links. Create one in your Dashboard in under a minute. You'll get a URL you can share via email, WhatsApp, or social media. Customers click it, see a Stripe-hosted checkout page, and pay. No code needed."

---

### Checkout (Hosted)

**What it is:** Stripe-hosted payment page with pre-built UI.
**Who uses it:** Merchants who want a polished checkout without building it.

| Feature | Detail |
|---------|--------|
| Hosting | Stripe-hosted (your logo/colors) |
| Features | Automatic tax, shipping, discounts, upsells |
| Payment methods | All enabled methods shown automatically |
| Conversion | Optimized by Stripe's data (billions of transactions) |
| Integration | Create Session -> redirect customer -> webhook on completion |

```python
session = stripe.checkout.Session.create(
    payment_method_types=["card", "sepa_debit"],
    line_items=[{
        "price": "price_abc123",
        "quantity": 1,
    }],
    mode="payment",  # or "subscription"
    success_url="https://yoursite.com/success",
    cancel_url="https://yoursite.com/cancel",
)
# Redirect customer to session.url
```

**vs. Payment Links:** Checkout requires some code but offers more customization (dynamic pricing, metadata, webhooks).

---

### Stripe.js & Elements

**What it is:** Client-side JavaScript library for building custom payment forms.
**Who uses it:** Merchants who want full UI control.

| Feature | Detail |
|---------|--------|
| Elements | Pre-built UI components (card input, IBAN, etc.) |
| Payment Element | Single component for ALL payment methods |
| Security | Card data never touches your server (PCI compliant) |
| Customization | Full CSS control |

**TAM recommendation order:**
1. Payment Links (no code)
2. Checkout (low code)
3. Elements (full control)

---

## Part 2: Billing & Subscriptions

### Billing

**What it is:** Recurring payments, invoicing, and subscription management.
**Who uses it:** SaaS, membership, any recurring business.

| Feature | Detail |
|---------|--------|
| Pricing models | Flat rate, per-seat, tiered, usage-based, metered |
| Invoicing | Automatic invoice generation and collection |
| Proration | Automatic when switching plans mid-cycle |
| Trials | Free trials with automatic conversion |
| Dunning | Smart Retries for failed payments (ML-based) |
| Tax | Stripe Tax integration |

### Key Objects

```
Product -> Price -> Subscription -> Invoice -> PaymentIntent
```

```python
# Create a product + price
product = stripe.Product.create(name="Pro Plan")
price = stripe.Price.create(
    product=product.id,
    unit_amount=2999,       # EUR 29.99/month
    currency="eur",
    recurring={"interval": "month"}
)

# Create subscription
subscription = stripe.Subscription.create(
    customer="cus_abc123",
    items=[{"price": price.id}],
    trial_period_days=14,
)
```

### Subscription Lifecycle

```
trialing -> active -> past_due -> canceled/unpaid
```

| Status | Meaning |
|--------|---------|
| `trialing` | In free trial period |
| `active` | Paying, all good |
| `past_due` | Payment failed, retrying |
| `canceled` | Subscription ended |
| `unpaid` | All retries exhausted |
| `paused` | Manually paused |
| `incomplete` | First payment pending |
| `incomplete_expired` | First payment failed |

### Smart Retries

Stripe's ML-based retry system for failed subscription payments:
- Analyzes billions of data points to choose optimal retry time
- Much better than fixed retry schedules
- Enable in: Dashboard -> Billing -> Settings -> Smart Retries

### Revenue Recovery

| Strategy | What it does |
|----------|-------------|
| Smart Retries | ML-optimized retry timing |
| Failed payment emails | Automatic email to customer |
| Card updater | Auto-update expired cards |
| Customer Portal | Self-service card update |

---

### Customer Portal

**What it is:** Stripe-hosted page where customers manage their own subscriptions.
**Who uses it:** Any merchant with subscriptions.

| Feature | Detail |
|---------|--------|
| Self-service | Update card, switch plan, cancel, view invoices |
| Hosting | Stripe-hosted (branded) |
| Setup | Dashboard configuration + 1 API call |
| Benefit | Reduces support tickets dramatically |

```python
# Create portal session
session = stripe.billing_portal.Session.create(
    customer="cus_abc123",
    return_url="https://yoursite.com/account",
)
# Redirect to session.url
```

**TAM talking point:** "Every subscription merchant should enable Customer Portal. It takes 10 minutes to set up and immediately reduces 'how do I cancel' support tickets to zero."

---

### Invoicing

**What it is:** Send invoices for one-time or recurring charges.

| Feature | Detail |
|---------|--------|
| Auto-invoicing | Generated automatically for subscriptions |
| Manual invoicing | Create and send via API or Dashboard |
| Payment | Hosted invoice page, auto-charge, or offline |
| PDF | Auto-generated, branded |
| Reminders | Automatic payment reminders |

---

## Part 3: Fraud & Risk

### Radar

**What it is:** ML-powered fraud detection built into every Stripe payment.
**Who uses it:** Every Stripe merchant (enabled by default).

| Tier | Features | Cost |
|------|----------|------|
| Radar (default) | ML fraud scoring, basic rules | Included |
| Radar for Fraud Teams | Custom rules, manual review, lists | Extra fee |

### Radar Rules

```
# Block high risk
Block if :risk_score: > 75

# 3DS for medium risk
Request 3D Secure if :risk_score: > 50

# Block country mismatch on high value
Block if :ip_country: != :card_country: AND :amount_in_eur: > 200

# Block prepaid cards
Block if :card_funding: = 'prepaid'

# Allow known customers
Allow if :is_recurring_customer:
```

### Risk Score

| Score Range | Risk Level | Recommended Action |
|-------------|-----------|-------------------|
| 0-20 | Very low | Allow |
| 20-50 | Low | Allow |
| 50-65 | Medium | Request 3DS |
| 65-75 | High | Request 3DS or review |
| 75-100 | Very high | Block |

**TAM talking points:**
- Default Radar catches ~90% of fraud with zero configuration
- Custom rules add precision for specific business patterns
- 3DS > blocking for medium risk (shifts liability, saves revenue)
- Monitor Visa 0.75% and Mastercard 1.0% fraud thresholds

---

### 3D Secure / SCA

**What it is:** Customer authentication required by PSD2 for EU card payments.

| Concept | Detail |
|---------|--------|
| PSD2 | EU regulation requiring Strong Customer Authentication |
| SCA | Strong Customer Authentication (the requirement) |
| 3DS | 3D Secure (the implementation) |
| 3DS2 | Modern version with better UX (in-app, biometric) |

### Exemptions (When 3DS Can Be Skipped)

| Exemption | Condition |
|-----------|-----------|
| Low value | Under EUR 30 |
| Recurring MIT | After initial authentication |
| TRA (Transaction Risk Analysis) | Low-risk by acquirer's assessment |
| Corporate cards | B2B corporate cards |
| Trusted beneficiary | Customer added merchant to whitelist |

**Stripe handles exemptions automatically.** Merchant just uses PaymentIntents — Stripe requests exemptions when appropriate, issuer decides.

---

## Part 4: Connect (Marketplaces & Platforms)

### What It Is

**Connect** lets platforms/marketplaces process payments on behalf of other businesses (sellers, drivers, freelancers).

### Account Types

| Type | KYC | Payout Control | Dashboard | Best For |
|------|-----|---------------|-----------|----------|
| Standard | Stripe handles | Seller controls | Full | Marketplaces where sellers manage themselves |
| Express | Stripe handles | Platform controls | Limited | Ride-sharing, delivery, gig platforms |
| Custom | Platform handles | Platform controls | None | Full white-label |

### Key Concepts

| Concept | What it means |
|---------|--------------|
| Connected Account | The seller/driver/freelancer's Stripe account |
| Platform Account | Your (the marketplace's) Stripe account |
| AccountLinks | Stripe-hosted onboarding form for sellers |
| Requirements | What Stripe needs from each seller (KYC) |
| Capabilities | What the account can do (accept payments, receive payouts) |

### Onboarding Flow

```python
# 1. Create connected account
account = stripe.Account.create(
    type="express",
    country="DE",
    capabilities={
        "card_payments": {"requested": True},
        "transfers": {"requested": True},
    },
)

# 2. Generate onboarding link
link = stripe.AccountLink.create(
    account=account.id,
    refresh_url="https://yoursite.com/reauth",
    return_url="https://yoursite.com/onboarding-complete",
    type="account_onboarding",
)
# Redirect seller to link.url

# 3. Listen for account.updated webhook
# Check: account.charges_enabled AND account.payouts_enabled
```

### Payment Flows

```python
# Direct charge (platform charges, seller receives)
charge = stripe.PaymentIntent.create(
    amount=10000,
    currency="eur",
    application_fee_amount=1500,  # Platform takes EUR 15
    stripe_account="acct_seller123",  # On behalf of seller
)

# Destination charge (platform charges, splits to seller)
charge = stripe.PaymentIntent.create(
    amount=10000,
    currency="eur",
    transfer_data={
        "destination": "acct_seller123",
        "amount": 8500,  # Seller gets EUR 85
    },
)

# Separate charges and transfers
pi = stripe.PaymentIntent.create(amount=10000, currency="eur")
transfer = stripe.Transfer.create(
    amount=8500,
    currency="eur",
    destination="acct_seller123",
)
```

**TAM recommendation:** Use destination charges for most marketplaces. Simplest to implement, automatic split.

---

## Part 5: Sigma (SQL Analytics)

**What it is:** SQL access to your complete Stripe data.
**Who uses it:** Data teams, finance, TAMs doing deep analysis.

| Feature | Detail |
|---------|--------|
| Access | Dashboard -> Sigma (or scheduled queries) |
| Language | SQL (Presto-based) |
| Data | Every Stripe object: charges, customers, subscriptions, etc. |
| Freshness | Near real-time (minutes) |
| Export | CSV download, scheduled email reports |
| Plan required | Scale or custom |

**TAM talking point:** "Sigma lets you answer any question about your payment data without writing code. 'What's our decline rate by country?' — that's one SQL query. 'Which customers churned after a failed payment?' — another query. It's the single best tool for understanding payment health."

---

## Part 6: Terminal (In-Person Payments)

**What it is:** Accept in-person payments with Stripe-certified hardware.
**Who uses it:** Retail, restaurants, events, pop-up shops.

| Feature | Detail |
|---------|--------|
| Hardware | BBPOS WisePOS E, Stripe Reader S700, M2 |
| Connection | Internet-connected to Stripe |
| Payment methods | Chip, tap (NFC), swipe, Apple/Google Pay |
| Integration | Same API as online payments (unified reporting) |
| Key benefit | One platform for online + in-person |

---

## Part 7: Atlas (Company Formation)

**What it is:** Incorporate a US company (Delaware C-corp) through Stripe.
**Who uses it:** International founders starting a US business.

| Feature | Detail |
|---------|--------|
| Entity | Delaware C-corp |
| Includes | EIN, bank account, Stripe account |
| Time | ~1-2 weeks |
| Cost | One-time fee |
| Best for | EU/international founders wanting US entity |

---

## Part 8: Treasury & Issuing

### Treasury

**What it is:** Banking-as-a-service. Embed financial accounts in your platform.

| Feature | Detail |
|---------|--------|
| Accounts | FDIC-insured financial accounts |
| Features | Store funds, send/receive ACH, wire transfers |
| Cards | Issue physical/virtual cards |
| Best for | Platforms that want to offer banking features |

### Issuing

**What it is:** Create, manage, and distribute payment cards.

| Feature | Detail |
|---------|--------|
| Card types | Virtual and physical |
| Brands | Visa |
| Controls | Spending limits, merchant categories, real-time auth |
| Best for | Expense management, corporate cards, fleet cards |

---

## Part 9: Tax

**What it is:** Automatic tax calculation and collection.

| Feature | Detail |
|---------|--------|
| Coverage | US sales tax, EU VAT, GST, etc. |
| Integration | Add to Checkout, Invoicing, or custom |
| Reporting | Tax filing reports |
| Real-time | Calculates per-transaction |

---

## Part 10: Identity

**What it is:** Verify customer identity documents.

| Feature | Detail |
|---------|--------|
| Verification | ID document + selfie matching |
| Documents | Passports, driver's licenses, ID cards |
| Markets | Global |
| Best for | KYC, age verification, fraud prevention |

---

## Part 11: Product Recommendation Matrix

When a merchant describes their need, recommend:

| Merchant Need | Recommend |
|--------------|-----------|
| "Accept online payments" | PaymentIntents + Elements |
| "I don't have a developer" | Payment Links |
| "Quick checkout page" | Checkout (hosted) |
| "Monthly subscriptions" | Billing |
| "Customers want to manage their subscription" | Customer Portal |
| "Marketplace with sellers" | Connect |
| "Reduce fraud" | Radar rules + 3DS |
| "Analyze payment data" | Sigma |
| "Accept in-store payments" | Terminal |
| "Send invoices" | Invoicing |
| "Calculate tax" | Tax |
| "Verify customer identity" | Identity |
| "Issue cards to employees" | Issuing |
| "Banking features in our app" | Treasury |
| "Incorporate a US company" | Atlas |
| "Comply with PSD2" | PaymentIntents (automatic) |

---

## Part 12: DACH-Specific Product Recommendations

| Market Need | Product | Why |
|-------------|---------|-----|
| German bank transfers | SEPA Direct Debit | Most popular non-card method in DE |
| Instant bank payment (DE) | Giropay | Real-time, trusted |
| Dutch customers | iDEAL | 60% of NL e-commerce |
| Buy now pay later (DACH) | Klarna | Popular with younger demographics |
| PSD2 compliance | PaymentIntents + 3DS | Automatic, no extra code |
| GDPR/DSGVO | Standard DPA | Stripe = data processor |
| Multi-country EU | Multi-currency + local methods | One integration, pan-EU |
| Swiss payments | Cards + SEPA (CHF + EUR) | Switzerland not in EU but uses SEPA |

**TAM talking point for DACH:**
> "For the German market specifically, I'd recommend enabling SEPA Direct Debit alongside cards. Many German consumers prefer direct debit — it's how they pay rent, utilities, and subscriptions. For younger demographics, Klarna is growing fast. And with PaymentIntents, your PSD2/SCA compliance is handled automatically."

---

## Part 13: Pricing (Know This for TAM Conversations)

| Product | Pricing Model |
|---------|--------------|
| Payments (EU cards) | 1.5% + EUR 0.25 per transaction |
| Payments (non-EU cards) | 2.5% + EUR 0.25 |
| SEPA Direct Debit | 0.35% (capped at EUR 5) |
| Currency conversion | 0.5-2% on top |
| Connect | Platform fee (varies) |
| Billing | 0.5% of recurring revenue |
| Radar for Fraud Teams | EUR 0.05 per screened transaction |
| Tax | 0.5% per transaction |
| Identity | EUR 1.50 per verification |
| Terminal | 2.7% + EUR 0.05 (in-person EU) |
| Sigma | Included in Scale plan |

*Prices may vary by region and volume. Always check stripe.com/pricing for current rates.*

---

*A TAM doesn't need to sell products — but you need to know which product solves which problem, instantly.*
