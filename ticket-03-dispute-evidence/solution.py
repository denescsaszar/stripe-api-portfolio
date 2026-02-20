"""
Ticket 03 — Dispute Evidence Submission
Account: Velora Fashion (Munich)
TAM Solution: List open disputes, check deadlines, submit evidence via the Stripe API.
"""

import os
import stripe
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# =============================================================================
# PART 1 — HOW THE DISPUTE LIFECYCLE WORKS
# =============================================================================
#
# 1. Customer files a chargeback with their bank
# 2. Stripe creates a Dispute object — status: needs_response
# 3. Funds are immediately debited from your balance (held by the bank)
# 4. You have a deadline (7–21 days) to submit evidence
# 5. Stripe forwards your evidence to the card network
# 6. Card network decides — status becomes: won or lost
# 7. If won: funds are returned. If lost: they are not.
#
# For product_not_received disputes, the strongest evidence is:
#   - Shipping tracking number (showing delivery confirmed)
#   - Customer signature or delivery confirmation
#   - Customer email at time of purchase
#   - Any communication showing the customer received the item
# =============================================================================


def list_open_disputes():
    """Fetch all disputes currently needing a response."""
    print("=" * 60)
    print("OPEN DISPUTES — Velora Fashion (Munich)")
    print("=" * 60)

    disputes = stripe.Dispute.list(limit=50)
    open_disputes = [d for d in disputes.auto_paging_iter()
                     if d["status"] == "needs_response"]

    if not open_disputes:
        print("No open disputes found.")
        print("Tip: create a test dispute with:")
        print("  stripe trigger charge.dispute.created")
        return []

    for dispute in open_disputes:
        deadline_ts = dispute.get("evidence_details", {}).get("due_by")
        if deadline_ts:
            deadline = datetime.fromtimestamp(deadline_ts, tz=timezone.utc)
            days_left = (deadline - datetime.now(tz=timezone.utc)).days
            deadline_str = deadline.strftime("%Y-%m-%d")
        else:
            deadline_str = "unknown"
            days_left = "?"

        print(f"\n  Dispute ID : {dispute['id']}")
        print(f"  Charge ID  : {dispute['charge']}")
        print(f"  Amount     : {dispute['amount'] / 100:.2f} {dispute['currency'].upper()}")
        print(f"  Reason     : {dispute['reason']}")
        print(f"  Status     : {dispute['status']}")
        print(f"  Deadline   : {deadline_str} ({days_left} days left)")

    print(f"\nTotal open disputes: {len(open_disputes)}")
    return open_disputes


def submit_evidence(dispute_id):
    """
    Submit evidence for a product_not_received dispute.
    In production, replace the placeholder strings with real data.
    """
    print(f"\n{'=' * 60}")
    print(f"SUBMITTING EVIDENCE — {dispute_id}")
    print("=" * 60)

    try:
        dispute = stripe.Dispute.modify(
            dispute_id,
            evidence={
                # Most important for product_not_received
                "shipping_tracking_number": "1Z999AA10123456784",
                "shipping_carrier": "DHL",
                "shipping_date": "2026-02-14",

                # Customer identity — proves they placed the order
                "customer_email_address": "customer@example.com",
                "customer_name": "Max Mustermann",

                # Written summary — the TAM's narrative to the card network
                "uncategorized_text": (
                    "The customer placed an order on 2026-02-12. "
                    "The order was shipped on 2026-02-14 via DHL with tracking "
                    "number 1Z999AA10123456784. DHL tracking confirms delivery "
                    "on 2026-02-16 at the customer's registered address. "
                    "We have attached the delivery confirmation."
                ),

                # submit=True sends it to Stripe — remove this to save as draft first
            },
            # Uncomment to submit immediately:
            # submit=True,
        )

        print(f"  Evidence saved as draft for dispute {dispute['id']}")
        print(f"  Status: {dispute['status']}")
        print(f"  Next step: review in Dashboard, then submit before deadline")
        print(f"  Dashboard: https://dashboard.stripe.com/disputes/{dispute['id']}")

    except stripe.error.InvalidRequestError as e:
        print(f"  Error: {e.user_message}")


def explain_evidence_strategy():
    """Print a TAM-level explanation of what wins product_not_received cases."""
    print(f"\n{'=' * 60}")
    print("EVIDENCE STRATEGY — product_not_received")
    print("=" * 60)
    print("""
  MUST HAVE (wins most cases):
  ✓ Tracking number showing delivery confirmed at customer's address
  ✓ Customer email address matching the order
  ✓ Clear written narrative explaining the timeline

  STRONG SUPPORTING EVIDENCE:
  ✓ Signed delivery confirmation from carrier
  ✓ Screenshot of customer's account activity after delivery
  ✓ Any customer communication (email, chat) post-purchase

  WHAT CARD NETWORKS LOOK FOR:
  - Proof the item left your warehouse (shipping label)
  - Proof it arrived at the right address (carrier scan)
  - Proof the customer had access to the account that ordered

  VELORA'S SITUATION:
  - DHL tracking numbers are strong evidence — DHL scans on delivery
  - Submit within 7 days for best outcome (don't wait for the deadline)
  - If the same customer disputes multiple orders, note the pattern
    in your uncategorized_text — card networks treat serial disputers differently
""")


if __name__ == "__main__":
    print("\nTicket 03 — Dispute Evidence Submission")
    print("Account: Velora Fashion (Munich)\n")

    # Step 1: list what's open and check deadlines
    open_disputes = list_open_disputes()

    # Step 2: explain the winning strategy
    explain_evidence_strategy()

    # Step 3: submit evidence for the first open dispute (demo)
    if open_disputes:
        submit_evidence(open_disputes[0]["id"])
    else:
        print("\nNo open disputes to submit evidence for.")
        print("To create a test dispute, run:")
        print("  stripe trigger charge.dispute.created")
        print("Then re-run this script.")
