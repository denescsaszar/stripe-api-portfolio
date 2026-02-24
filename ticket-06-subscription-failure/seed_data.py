"""
seed_data.py — Create test subscriptions with failing payment methods.
This generates invoices that will fail, so we can test the diagnostic script.
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stripe test payment method IDs that trigger specific failures
TEST_PAYMENT_METHODS = [
    ("pm_card_chargeDeclined", "Card declined"),
    ("pm_card_chargeDeclinedInsufficientFunds", "Insufficient funds"),
    ("pm_card_chargeDeclinedExpiredCard", "Expired card"),
    ("pm_card_chargeDeclinedIncorrectCvc", "Incorrect CVC"),
    ("pm_card_visa", "Visa success (for control)"),
]

def create_test_subscription(payment_method_id, description):
    """Create a test subscription with a specific payment method."""
    try:
        # Create customer
        customer = stripe.Customer.create(
            email=f"test-{description.lower().replace(' ', '-')}@audiblebooks.test",
            payment_method=payment_method_id,
            invoice_settings={"default_payment_method": payment_method_id},
        )
        
        # Create a test product and price if needed
        # For now, we'll use a generic price ID (you may need to create this in Dashboard)
        # Alternatively, create a simple product+price
        try:
            product = stripe.Product.create(
                name="Audiobook Subscription",
                type="service",
            )
            price = stripe.Price.create(
                product=product.id,
                unit_amount=999,  # €9.99
                currency="eur",
                recurring={"interval": "month", "interval_count": 1},
            )
            price_id = price.id
        except:
            # If product creation fails, use a fallback
            print(f"  Note: Using test price. In production, create price in Dashboard.")
            price_id = "price_1ABC"  # Dummy — won't work but script continues
        
        # Create subscription — this will trigger payment
        sub = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            payment_behavior="error_if_incomplete",  # Don't retry — just error
        )
        
        print(f"  ✓ {description:30} → {sub.id}")
        return sub.id
    
    except stripe.error.CardError as e:
        # Expected for declined cards
        print(f"  ✗ {description:30} → {e.user_message}")
        return None
    except Exception as e:
        print(f"  ! {description:30} → {str(e)[:50]}")
        return None

print("Creating test subscriptions with various payment failures...\n")

for pm_id, desc in TEST_PAYMENT_METHODS:
    create_test_subscription(pm_id, desc)

print("\nDone. Now run solution.py to see the diagnostic report:")
print("  python3 ticket-06-subscription-failure/solution.py")
