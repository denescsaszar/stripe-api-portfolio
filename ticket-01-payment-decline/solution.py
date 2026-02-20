"""
Ticket 01 — Payment Decline Investigation
Diagnose a spike in failed payments by analysing decline codes
from recent PaymentIntents.
"""

import os
import stripe
from collections import Counter
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


ISSUER_DECLINES = {
    "insufficient_funds": "Customer's card has insufficient funds.",
    "do_not_honor": "Issuer blocked the charge — generic decline.",
    "card_declined": "Card declined — reason not specified by issuer.",
    "lost_card": "Card reported lost.",
    "stolen_card": "Card reported stolen.",
    "expired_card": "Card is expired.",
    "incorrect_cvc": "Wrong CVC entered.",
    "card_velocity_exceeded": "Too many charges on this card recently.",
}

STRIPE_BLOCKS = {
    "fraudulent": "Stripe/Radar blocked as likely fraud.",
    "merchant_blacklist": "Card is on your Radar block list.",
}


def fetch_failed_payment_intents(limit=100):
    """Fetch recent failed PaymentIntents from the Stripe API."""
    results = []
    payment_intents = stripe.PaymentIntent.list(limit=limit)

    for pi in payment_intents.auto_paging_iter():
        if pi.status == "requires_payment_method" and pi.last_payment_error:
            results.append(pi)
        if len(results) >= limit:
            break

    return results


def analyse_declines(failed_intents):
    """Group failures by decline code and classify root cause."""
    decline_codes = []

    for pi in failed_intents:
        error = pi.last_payment_error
        code = error.decline_code or error.code or "unknown"
        decline_codes.append(code)

    return Counter(decline_codes)


def print_diagnostic_report(total_fetched, failed_intents, counter):
    """Print a clean summary a TAM can share directly with the merchant."""
    total_failed = len(failed_intents)
    failure_rate = (total_failed / total_fetched * 100) if total_fetched else 0

    print("=" * 55)
    print("  STRIPE DECLINE DIAGNOSTIC — TechGear GmbH")
    print("=" * 55)
    print(f"  Payment intents analysed : {total_fetched}")
    print(f"  Failed                   : {total_failed}")
    print(f"  Failure rate             : {failure_rate:.1f}%")
    print("-" * 55)
    print("  BREAKDOWN BY DECLINE CODE")
    print("-" * 55)

    for code, count in counter.most_common():
        pct = count / total_failed * 100
        category = "Issuer" if code in ISSUER_DECLINES else \
                   "Stripe/Radar" if code in STRIPE_BLOCKS else "Other"
        explanation = ISSUER_DECLINES.get(code) or \
                      STRIPE_BLOCKS.get(code) or "No standard explanation."
        print(f"  [{category}] {code} — {count}x ({pct:.1f}%)")
        print(f"    → {explanation}")

    print("=" * 55)
    print("  RECOMMENDATION")
    print("-" * 55)

    top_code = counter.most_common(1)[0][0] if counter else None

    if top_code in ISSUER_DECLINES:
        print("  Dominant cause: issuer-side declines.")
        print("  → No integration fix needed on merchant side.")
        print("  → Advise merchant to review checkout UX (card retry,")
        print("    clear error messages, offer alternative methods")
        print("    such as SEPA Direct Debit or Klarna for DE market).")
    elif top_code in STRIPE_BLOCKS:
        print("  Dominant cause: Stripe/Radar blocks.")
        print("  → Review Radar rules in the Dashboard.")
        print("  → Check if a recent rule change is over-blocking.")
    else:
        print("  Mixed decline pattern — manual review recommended.")
        print("  → Share full breakdown with merchant and Stripe support.")

    print("=" * 55)


def main():
    print("Fetching failed PaymentIntents...\n")
    all_intents = list(stripe.PaymentIntent.list(limit=100).auto_paging_iter())
    failed = [pi for pi in all_intents
              if pi.status == "requires_payment_method" and pi.last_payment_error]

    if not failed:
        print("No failed PaymentIntents found in test data.")
        print("Tip: use the Stripe CLI to trigger test declines:")
        print("  stripe trigger payment_intent.payment_failed")
        return

    counter = analyse_declines(failed)
    print_diagnostic_report(len(all_intents), failed, counter)


if __name__ == "__main__":
    main()
