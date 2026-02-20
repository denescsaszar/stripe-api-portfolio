"""
seed_data.py — Generate test PaymentIntents for the diagnostic demo.
Uses Stripe's built-in test payment method IDs (no raw card numbers needed).
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stripe's built-in test payment method IDs
TEST_CASES = [
    ("pm_card_visa",                "Visa success",        "success"),
    ("pm_card_visa",                "Visa success",        "success"),
    ("pm_card_visa",                "Visa success",        "success"),
    ("pm_card_chargeDeclined",      "Generic decline",     "fail"),
    ("pm_card_chargeDeclined",      "Generic decline",     "fail"),
    ("pm_card_chargeDeclinedInsufficientFunds", "Insufficient funds", "fail"),
    ("pm_card_chargeDeclinedInsufficientFunds", "Insufficient funds", "fail"),
    ("pm_card_chargeDeclinedInsufficientFunds", "Insufficient funds", "fail"),
    ("pm_card_chargeDeclinedExpiredCard",       "Expired card",       "fail"),
    ("pm_card_chargeDeclinedIncorrectCvc",      "Incorrect CVC",      "fail"),
]

def create_payment(pm_id, description):
    try:
        intent = stripe.PaymentIntent.create(
            amount=18000,
            currency="eur",
            payment_method=pm_id,
            confirm=True,
            return_url="https://example.com",
        )
        print(f"  ✓ {description} — {intent.status}")
    except stripe.error.CardError as e:
        print(f"  ✗ {description} — {e.error.decline_code or e.error.code}")
    except Exception as e:
        print(f"  ! {description} — unexpected error: {e}")

print("Seeding test PaymentIntents...\n")
for pm_id, desc, _ in TEST_CASES:
    create_payment(pm_id, desc)
print("\nDone. Now run solution.py to see the diagnostic report.")
