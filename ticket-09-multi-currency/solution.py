"""
Ticket 09: Multi-Currency Payment Setup
================================
Solution for GlobeShop Ltd - expanding to EU and Asia

Demonstrates:
- Currency detection and selection
- Multi-currency PaymentIntent creation
- Exchange rate handling and Stripe's pricing
- Multi-currency account configuration
- Settlement and reporting across currencies
- Regional considerations (PSD2, post-Brexit, etc.)
"""

import stripe
import os
from datetime import datetime

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# GlobeShop's merchant configuration
MERCHANT_CONFIG = {
    "business_name": "GlobeShop Ltd",
    "location": "London, UK",
    "default_currency": "gbp",
    "account_id": None,  # Would be merchant's Stripe account
}

# Supported currencies for expansion (GlobeShop's markets)
SUPPORTED_CURRENCIES = {
    "gbp": {"country": "UK", "symbol": "£", "region": "Europe"},
    "usd": {"country": "USA", "symbol": "$", "region": "Americas"},
    "eur": {"country": "EU", "symbol": "€", "region": "Europe"},
    "jpy": {"country": "Japan", "symbol": "¥", "region": "Asia"},
    "aud": {"country": "Australia", "symbol": "A$", "region": "Oceania"},
}

# Approximate Stripe exchange rates (for demonstration)
# Real implementation would use Stripe's live rates
STRIPE_EXCHANGE_RATES = {
    "gbp_to_usd": 1.27,
    "gbp_to_eur": 1.17,
    "gbp_to_jpy": 189.50,
    "gbp_to_aud": 2.43,
}

# Stripe's pricing for currency pairs (varies by pair)
# Usually 0.8-1.5% - showing typical range
STRIPE_FEE_BY_PAIR = {
    ("gbp", "gbp"): 1.4,  # Same currency, standard UK rate
    ("gbp", "usd"): 2.2,  # GBP->USD conversion fee
    ("gbp", "eur"): 1.8,  # GBP->EUR, lower fee (both EU)
    ("gbp", "jpy"): 2.5,  # GBP->JPY, higher fee (volatile pair)
    ("gbp", "aud"): 2.3,  # GBP->AUD, high fee
}


# ============================================================================
# PART 1: CURRENCY DETECTION & SELECTION
# ============================================================================

def detect_customer_currency(customer_ip: str = None, customer_country: str = None) -> str:
    """
    Detect customer's preferred currency based on location.
    
    In production, this would:
    1. Use customer's IP to geo-locate
    2. Check their browser language preferences
    3. Remember their previous choices
    4. Show them an option to override
    
    For now, we'll simulate based on country.
    """
    
    country_to_currency = {
        "US": "usd",
        "UK": "gbp",
        "DE": "eur",
        "FR": "eur",
        "JP": "jpy",
        "AU": "aud",
    }
    
    detected = country_to_currency.get(customer_country, "gbp")  # Default to GBP
    return detected


def get_local_amount(base_amount_gbp: float, target_currency: str) -> float:
    """
    Convert base amount (in GBP) to customer's local currency.
    
    Example: Customer in Japan wants to buy £20 item
    -> Convert to ¥3,790 (¥ = GBP * 189.50)
    """
    
    if target_currency == "gbp":
        return base_amount_gbp
    
    rate_key = f"gbp_to_{target_currency}"
    rate = STRIPE_EXCHANGE_RATES.get(rate_key, 1.0)
    
    return round(base_amount_gbp * rate, 2)


# ============================================================================
# PART 2: MULTI-CURRENCY PAYMENTINTENTS
# ============================================================================

def create_multi_currency_payment(
    order_id: str,
    amount_gbp: float,
    customer_country: str = "US",
    charge_in_local_currency: bool = True
) -> dict:
    """
    Create PaymentIntent in customer's local currency.
    
    Key decision: Charge in local currency vs. merchant's default?
    
    Pros of local currency:
    - Better conversion rates (customers see familiar amounts)
    - Lower decline rates
    - Better for compliance (PSD2, etc.)
    
    Cons:
    - Exchange rate risk if settlement is delayed
    - More complex reporting
    
    GlobeShop's strategy: Charge in customer's local currency
    to maximize conversion and minimize payment friction.
    """
    
    # Detect customer's currency
    customer_currency = detect_customer_currency(
        customer_country=customer_country
    )
    
    # Convert amount
    if charge_in_local_currency:
        payment_amount = get_local_amount(amount_gbp, customer_currency)
        currency = customer_currency
    else:
        # Fallback: charge in GBP (merchant's default)
        payment_amount = amount_gbp * 100  # Stripe uses cents
        currency = "gbp"
    
    # Convert to cents for Stripe API
    amount_cents = int(payment_amount * 100)
    
    # Create PaymentIntent using test payment method
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        payment_method="pm_card_visa",
        confirm=True,
        return_url="https://mystore.com/checkout/success",
        metadata={
            "order_id": order_id,
            "customer_country": customer_country,
            "customer_currency": currency,
            "base_amount_gbp": str(amount_gbp),
            "merchant_name": MERCHANT_CONFIG["business_name"],
        },
        description=f"Order {order_id} - GlobeShop Ltd"
    )
    
    return {
        "order_id": order_id,
        "customer_country": customer_country,
        "base_amount_gbp": amount_gbp,
        "payment_currency": currency,
        "payment_amount": payment_amount,
        "amount_cents": amount_cents,
        "intent_id": intent.id,
        "status": intent.status,
        "success": intent.status == "succeeded"
    }



# ============================================================================
# PART 3: UNDERSTANDING EXCHANGE RATES & FEES
# ============================================================================

def explain_exchange_rates_and_fees(base_currency: str = "gbp"):
    """
    Explain how Stripe's exchange rates and fees work.
    
    KEY CONCEPT: Interchange fees vary by currency pair.
    """
    
    print("\n" + "="*80)
    print("EXCHANGE RATES & FEES EXPLANATION")
    print("="*80)
    
    print(f"\nMerchant's base currency: {base_currency.upper()}")
    print(f"Settlement currency: {base_currency.upper()} (to {MERCHANT_CONFIG['location']} bank)")
    
    print("\nStripe's exchange rates (live rates vary):")
    for rate_key, rate in STRIPE_EXCHANGE_RATES.items():
        from_curr, to_curr = rate_key.split("_to_")
        print(f"  {from_curr.upper()} → {to_curr.upper()}: 1 {from_curr.upper()} = {rate} {to_curr.upper()}")
    
    print("\nStripe's pricing by currency pair (GBP merchant):")
    for (from_curr, to_curr), fee in STRIPE_FEE_BY_PAIR.items():
        if from_curr == base_currency:
            print(f"  {from_curr.upper()} → {to_curr.upper()}: {fee}% (includes card network & processing)")
    
    print("\nKey insights:")
    print("  • Stripe's rates are competitive vs. traditional payment processors")
    print("  • Same currency charges (GBP→GBP) have slightly lower fees")
    print("  • Some pairs (EUR/USD) have lower fees due to high volume")
    print("  • Cross-border fees reflect actual FX risk + network costs")
    print("  • Volatile pairs (GBP/JPY) have higher fees")


# ============================================================================
# PART 4: MULTI-CURRENCY BALANCE & SETTLEMENT
# ============================================================================

def retrieve_multi_currency_balance():
    """
    Retrieve balance across all currencies.
    
    In multi-currency setup, balance is broken down by currency.
    Settlement can happen in any supported currency, though fees apply
    if converting to a non-primary currency.
    """
    
    print("\n" + "="*80)
    print("MULTI-CURRENCY BALANCE BREAKDOWN")
    print("="*80)
    
    balance = stripe.Balance.retrieve()
    
    print(f"\nBalance retrieved at: {datetime.now().isoformat()}")
    
    # Available balance (ready to payout)
    print("\nAVAILABLE BALANCE (can be paid out immediately):")
    if balance['available']:
        for curr_balance in balance['available']:
            amount = curr_balance['amount'] / 100
            currency = curr_balance['currency'].upper()
            print(f"  {currency}: {amount:.2f} (available to settle)")
    else:
        print("  (No balance available)")
    
    # Pending balance (waiting for hold to lift)
    print("\nPENDING BALANCE (2-7 day hold):")
    if balance['pending']:
        for curr_balance in balance['pending']:
            amount = curr_balance['amount'] / 100
            currency = curr_balance['currency'].upper()
            print(f"  {currency}: {amount:.2f} (pending hold)")
    else:
        print("  (No pending balance)")
    
    # Instant payout balance (if enabled)
    print("\nINSTANT PAYOUT BALANCE (if instant payouts enabled):")
    if balance.get('instant_available'):
        for curr_balance in balance['instant_available']:
            amount = curr_balance['amount'] / 100
            currency = curr_balance['currency'].upper()
            print(f"  {currency}: {amount:.2f} (instant available)")
    else:
        print("  (Not enabled for this account)")


# ============================================================================
# PART 5: SMART CURRENCY ROUTING & SETTLEMENT
# ============================================================================

def explain_settlement_strategy():
    """
    Explain GlobeShop's multi-currency settlement strategy.
    """
    
    print("\n" + "="*80)
    print("SETTLEMENT & REPORTING STRATEGY")
    print("="*80)
    
    print("\nGlobeShop's Approach:")
    print("1. Charge customers in their local currency (best for conversions)")
    print("2. Settle in GBP (default) weekly")
    print("3. Hold 2-3 days for fraud review (standard)")
    print("4. Monitor balances by currency in Dashboard")
    
    print("\nAlternative approaches (if they change strategy):")
    print("\nOption A: Charge in GBP always")
    print("  ✓ Simpler accounting")
    print("  ✓ No FX risk on settlement")
    print("  ✗ Higher decline rates")
    print("  ✗ Worse customer experience")
    
    print("\nOption B: Charge in local, settle in local")
    print("  ✓ No conversion fees on settlement")
    print("  ✓ Better for tax reporting")
    print("  ✗ Need separate bank accounts per currency")
    print("  ✗ More complex reconciliation")
    
    print("\nOption C: Mixed approach by region")
    print("  ✓ EU customers in EUR (PSD2 compliant)")
    print("  ✓ US customers in USD (standard)")
    print("  ✓ Other customers in GBP")
    print("  ✗ More logic in checkout")
    
    print("\nRegional Considerations:")
    print("  • EU (PSD2): Strong Customer Auth required for remote cards")
    print("    → Stripe handles this with PaymentIntents")
    print("  • UK (post-Brexit): Still uses £ for all customers")
    print("  • APAC (Japan/AU): High demand for local currencies")
    print("  • All regions: Vary FX rates daily")


# ============================================================================
# PART 6: WEBHOOK HANDLING FOR MULTI-CURRENCY
# ============================================================================

def show_webhook_example():
    """
    Show webhook structure for multi-currency payments.
    """
    
    print("\n" + "="*80)
    print("WEBHOOK HANDLING FOR MULTI-CURRENCY CHARGES")
    print("="*80)
    
    print("""
    @app.route('/webhooks/stripe', methods=['POST'])
    def webhook():
        event = verify_webhook_signature(request)
        
        if event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            
            # Extract multi-currency info
            customer_country = intent.metadata.get('customer_country')
            customer_currency = intent.metadata.get('customer_currency')
            base_amount_gbp = intent.metadata.get('base_amount_gbp')
            
            # Log for reporting
            log_multi_currency_charge(
                intent.id,
                amount=intent.amount / 100,
                currency=intent.currency,
                customer_currency=customer_currency,
                customer_country=customer_country
            )
            
            # Fulfill order
            fulfill_order(intent.metadata['order_id'])
        
        return "Received", 200
    """)


# ============================================================================
# DEMO & OUTPUT
# ============================================================================

def main():
    """Run the complete multi-currency demo."""
    
    print("\n" + "="*80)
    print("GLOBESHOP LTD - MULTI-CURRENCY PAYMENT SETUP")
    print("="*80)
    print(f"\nMerchant: {MERCHANT_CONFIG['business_name']}")
    print(f"Location: {MERCHANT_CONFIG['location']}")
    print(f"Default Currency: {MERCHANT_CONFIG['default_currency'].upper()}")
    
    # Part 1: Show supported currencies
    print("\n" + "-"*80)
    print("SUPPORTED CURRENCIES & MARKETS")
    print("-"*80)
    for curr, info in SUPPORTED_CURRENCIES.items():
        print(f"  {curr.upper()}: {info['country']} ({info['region']})")
    
    # Part 2: Demonstrate multi-currency charges
    print("\n" + "-"*80)
    print("MULTI-CURRENCY CHARGE EXAMPLES")
    print("-"*80)
    
    test_scenarios = [
        {"order_id": "ORDER_001", "amount_gbp": 20, "country": "US"},
        {"order_id": "ORDER_002", "amount_gbp": 20, "country": "DE"},
        {"order_id": "ORDER_003", "amount_gbp": 20, "country": "JP"},
        {"order_id": "ORDER_004", "amount_gbp": 20, "country": "AU"},
        {"order_id": "ORDER_005", "amount_gbp": 20, "country": "UK"},
    ]
    
    results = []
    for scenario in test_scenarios:
        print(f"\nScenario: {scenario['order_id']} from {scenario['country']}")
        result = create_multi_currency_payment(
            order_id=scenario['order_id'],
            amount_gbp=scenario['amount_gbp'],
            customer_country=scenario['country']
        )
        results.append(result)
        
        print(f"  Amount in GBP: £{result['base_amount_gbp']}")
        print(f"  Customer currency: {result['payment_currency'].upper()}")
        print(f"  Amount charged: {result['payment_currency'].upper()}{result['payment_amount']}")
        print(f"  Status: {result['status']}")
        print(f"  Success: {'✓ Yes' if result['success'] else '✗ No'}")
    
    # Part 3: Explain rates and fees
    explain_exchange_rates_and_fees()
    
    # Part 4: Show balance
    retrieve_multi_currency_balance()
    
    # Part 5: Settlement strategy
    explain_settlement_strategy()
    
    # Part 6: Webhook example
    show_webhook_example()
    
    # Summary
    print("\n" + "="*80)
    print("TAM SUMMARY FOR GLOBESHOP")
    print("="*80)
    print("""
    What we've covered:
    
    1. ✓ Currency detection - Automatically detect customer location
    2. ✓ Local currency charging - Charge in customer's currency
    3. ✓ Exchange rates - Understand Stripe's competitive rates
    4. ✓ Fee optimization - Know which pairs are cheaper
    5. ✓ Multi-currency balance - View funds by currency
    6. ✓ Settlement strategy - Choose when/how to settle
    7. ✓ Regional compliance - PSD2 for EU, etc.
    
    Next steps for GlobeShop:
    
    1. Implement currency detection in checkout flow
    2. Configure multi-currency account in Stripe Dashboard
    3. Set up webhooks to handle charges by currency
    4. Test with all supported currencies in test mode
    5. Monitor balance and settlement across currencies
    6. Review daily/weekly reports by currency
    7. Adjust strategy based on customer decline rates
    
    Key metrics to monitor:
    - Conversion rate by currency (is local currency better?)
    - Decline rate by currency (some may have higher risk)
    - Fees by currency pair (optimize settlement)
    - Customer feedback on currency options
    - Chargeback rate by region
    
    Stripe's advantage:
    - No limits on currency pairs
    - Competitive FX rates (mid-market +0.5-2% vs 2-3% for traditional)
    - Automatic PSD2 compliance for all EU transactions
    - Easy reporting by currency in Dashboard
    """)
    
    return results


if __name__ == "__main__":
    results = main()
    print("\n" + "="*80)
    print(f"Completed {len([r for r in results if r['success']])} successful charges")
    print("="*80 + "\n")
