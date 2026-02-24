"""
Ticket 04 — Custom Radar Rules for Fraud Prevention
Account: SportDeal GmbH (Frankfurt)
TAM Solution: Radar rule strategy + risk score analysis via the Stripe API.
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# =============================================================================
# PART 1 — HOW STRIPE RADAR WORKS
# =============================================================================
#
# Every payment that goes through Stripe is scored by Radar (0–100).
# Score 0 = very low risk. Score 100 = almost certainly fraud.
#
# Radar runs two layers:
#
# 1. DEFAULT RULES (all accounts)
#    - Blocks cards on Stripe's global fraud network blocklist
#    - Blocks cards with a very high risk score
#    - Blocks payments from sanctioned countries
#    - These run automatically — you can't turn them off
#
# 2. CUSTOM RULES (Radar for Fraud Teams — paid add-on)
#    - You write your own if/then logic
#    - Three actions: Block, Review, Allow (Allow overrides block rules)
#    - Rules are evaluated in order — first match wins
#    - You can use: amount, country, email, card brand, risk score,
#      metadata, IP country, and more
#
# SportDeal's problem: fraud rate 1.8% — above Visa's 0.75% threshold.
# If they exceed 0.9% for too long, Stripe can place them on a monitoring
# programme which adds fees and scrutiny.
# =============================================================================


# =============================================================================
# PART 2 — RECOMMENDED RADAR RULES FOR SPORTDEAL
# =============================================================================
#
# These rules should be entered in the Stripe Dashboard under:
# Radar → Rules → Add rule
#
# You cannot create Radar rules via the API — they must be set in the Dashboard.
# But we document them here so they can be version-controlled and reviewed.

RADAR_RULES = [
    {
        "action": "Block",
        "rule": "if :risk_score: >= 75 then block",
        "reason": (
            "Block payments with a Radar risk score of 75 or above. "
            "Default threshold is 85 — lowering to 75 catches more fraud "
            "at the cost of some false positives. Monitor for 1 week before "
            "adjusting further."
        ),
    },
    {
        "action": "Review",
        "rule": "if :risk_score: >= 60 and :amount_in_gbp: > 150 then review",
        "reason": (
            "Flag high-value orders with elevated risk for manual review "
            "instead of blocking. Protects revenue while adding a safety check. "
            "SportDeal's fraud pattern is high-value items — this targets it directly."
        ),
    },
    {
        "action": "Block",
        "rule": "if :ip_country: != :card_country: and :amount_in_eur: > 200 then block",
        "reason": (
            "Block high-value orders where the IP country doesn't match the "
            "card's country. A German customer using a French card is fine — "
            "but an IP from outside Europe using a European card for €200+ "
            "is a strong fraud signal for SportDeal's customer base."
        ),
    },
    {
        "action": "Review",
        "rule": "if :is_new_customer: = true and :amount_in_eur: > 300 then review",
        "reason": (
            "Send new customers spending over €300 to manual review. "
            "Legitimate first-time high-value purchases are rare — "
            "this catches the pattern SportDeal reported without blocking outright."
        ),
    },
    {
        "action": "Block",
        "rule": "if :card_funding: = 'prepaid' and :amount_in_eur: > 100 then block",
        "reason": (
            "Prepaid cards are anonymous and cannot be traced — "
            "a common choice for fraud. Blocking prepaid cards over €100 "
            "cuts a significant fraud vector with minimal legitimate customer impact."
        ),
    },
]


def print_radar_rules():
    print("=" * 60)
    print("RECOMMENDED RADAR RULES — SportDeal GmbH")
    print("=" * 60)
    print("Enter these in: Dashboard → Radar → Rules → Add rule\n")

    for i, rule in enumerate(RADAR_RULES, 1):
        print(f"  Rule {i} [{rule['action'].upper()}]")
        print(f"  Syntax : {rule['rule']}")
        print(f"  Reason : {rule['reason']}")
        print()


# =============================================================================
# PART 3 — QUERY RADAR RISK SCORES VIA THE API
# =============================================================================

def analyse_radar_scores(limit=50):
    """
    Pull recent PaymentIntents and extract Radar risk scores.
    Shows the distribution of risk across recent transactions.
    """
    print("=" * 60)
    print("RADAR RISK SCORE ANALYSIS — recent transactions")
    print("=" * 60)

    intents = stripe.PaymentIntent.list(limit=limit)

    scores = {"low (0-39)": 0, "medium (40-74)": 0, "high (75-100)": 0, "no score": 0}
    high_risk = []

    for pi in intents.auto_paging_iter():
        outcome = pi.get("charges", {}).get("data", [{}])[0].get("outcome", {})
        score = outcome.get("risk_score")

        if score is None:
            scores["no score"] += 1
        elif score >= 75:
            scores["high (75-100)"] += 1
            high_risk.append((pi["id"], score, pi["amount"] / 100, pi["currency"].upper()))
        elif score >= 40:
            scores["medium (40-74)"] += 1
        else:
            scores["low (0-39)"] += 1

    print(f"\n  Transactions analysed: {limit}")
    for band, count in scores.items():
        print(f"  {band}: {count}")

    if high_risk:
        print(f"\n  HIGH RISK TRANSACTIONS (score >= 75):")
        for pid, score, amount, currency in high_risk:
            print(f"    {pid} — score: {score} — {amount:.2f} {currency}")
    else:
        print("\n  No high-risk transactions found in this sample.")


# =============================================================================
# PART 4 — BLOCK VS. 3DS TRADE-OFF
# =============================================================================
#
# BLOCKING: Hard stop. Payment is rejected immediately.
#   + Prevents the fraudulent charge entirely
#   - Also blocks legitimate customers who look risky (false positives)
#   - Lost revenue from good customers is invisible but real
#
# 3D SECURE (3DS): Adds a bank authentication step (OTP, biometric).
#   + Shifts fraud liability to the card issuer — you don't pay the chargeback
#   + Legitimate customers can still complete the payment
#   - Adds friction — some customers drop off at the 3DS step (~10-15%)
#   - Doesn't prevent the charge, just shifts who pays if it's fraudulent
#
# RECOMMENDATION FOR SPORTDEAL:
#   - Score >= 75: Block (too risky, protect the fraud rate metric)
#   - Score 60-74, amount > €150: Review (manual check before fulfilling)
#   - Score 40-59, new customer: Request 3DS (friction without hard block)
#   - Score < 40: Allow (normal flow)
#
# This layered approach reduces fraud rate without gutting conversion.
# =============================================================================


if __name__ == "__main__":
    print("\nTicket 04 — Custom Radar Rules for Fraud Prevention")
    print("Account: SportDeal GmbH (Frankfurt)\n")

    print_radar_rules()
    analyse_radar_scores(limit=50)

    print("\n" + "=" * 60)
    print("BLOCK VS. 3DS TRADE-OFF SUMMARY")
    print("=" * 60)
    print("""
  Score >= 75      → BLOCK   (fraud rate protection)
  Score 60-74,     → REVIEW  (manual check, high-value orders)
  amount > €150
  Score 40-59,     → 3DS     (friction, liability shift)
  new customer
  Score < 40       → ALLOW   (normal checkout flow)

  Radar rules: Dashboard → Radar → Rules → Add rule
  Test first:  use test mode cards with risk_score metadata
  Monitor:     Radar → Overview for block/review/pass breakdown
""")
