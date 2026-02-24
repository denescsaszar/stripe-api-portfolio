"""
Ticket 06 — Subscription Invoice Failure & Smart Retry
Diagnose failed invoices and implement intelligent retry logic.
"""

import os
import stripe
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ─── FAILURE CLASSIFICATION ──────────────────────────────────────────────

TEMPORARY_FAILURES = {
    "try_again": "Temporary issue — retry immediately or after short delay",
    "processing_error": "Stripe's systems had a hiccup — safe to retry",
    "rate_limited": "Too many requests — back off and retry",
}

PERMANENT_FAILURES = {
    "card_declined": "Card issuer declined — customer needs different card",
    "insufficient_funds": "Insufficient funds — customer needs to add funds",
    "lost_card": "Card reported lost — customer must use different card",
    "stolen_card": "Card reported stolen — customer must use different card",
    "expired_card": "Card expired — customer must update card details",
    "incorrect_cvc": "Wrong CVC — ask customer to verify card",
    "do_not_honor": "Issuer blocked — likely fraud block, customer calls issuer",
}

REQUIRES_ACTION = {
    "action_required": "Customer must complete 3D Secure or other action",
    "authentication_required": "Payment needs authentication",
}


def fetch_failed_invoices(limit=50):
    """Fetch recent invoices that failed payment."""
    failed = []
    
    # Check multiple statuses where failures might appear
    for status in ["draft", "open", "uncollectible"]:
        invoices = stripe.Invoice.list(status=status, limit=limit)
        
        for inv in invoices.auto_paging_iter():
            # Look for invoices with payment errors
            if inv.last_finalization_error or status == "uncollectible":
                failed.append(inv)
            if len(failed) >= limit:
                break
        
        if len(failed) >= limit:
            break
    
    return failed


def classify_failure(invoice):
    """Classify why an invoice failed."""
    error = invoice.last_finalization_error
    if not error:
        return "UNKNOWN", "no_error"
    
    code = error.get("code") or error.get("type")
    
    if code in TEMPORARY_FAILURES:
        return "TEMPORARY", code
    elif code in PERMANENT_FAILURES:
        return "PERMANENT", code
    elif code in REQUIRES_ACTION:
        return "ACTION_REQUIRED", code
    else:
        return "UNKNOWN", code


def should_retry(category, retry_count=0):
    """Decide if we should retry based on failure category."""
    if category == "TEMPORARY":
        return retry_count < 3  # Max 3 retries for temporary failures
    elif category == "ACTION_REQUIRED":
        return False  # Don't retry — customer must take action
    elif category == "PERMANENT":
        return False  # Don't retry — card is genuinely blocked
    else:
        return retry_count < 1  # Unknown — try once more


def retry_invoice(invoice_id):
    """Attempt to retry payment on a failed invoice."""
    try:
        # pay_invoice attempts to pay an open invoice
        invoice = stripe.Invoice.pay(invoice_id)
        return True, invoice.status
    except stripe.error.CardError as e:
        return False, f"Card error: {e.user_message}"
    except stripe.error.StripeError as e:
        return False, f"Stripe error: {str(e)}"


def get_demo_failed_invoices():
    """Return mock failed invoices for demonstration."""
    class MockInvoice:
        def __init__(self, inv_id, email, amount, code, message):
            self.id = inv_id
            self.customer_email = email
            self.amount_due = amount
            self.currency = "eur"
            self.last_finalization_error = {
                "code": code,
                "type": code,
                "message": message,
            }
    
    return [
        MockInvoice("in_demo_001", "maria@audiblebooks.at", 999, "card_declined", "Your card was declined."),
        MockInvoice("in_demo_002", "franz@example.com", 999, "insufficient_funds", "Your card has insufficient funds."),
        MockInvoice("in_demo_003", "anna@example.at", 999, "expired_card", "Your card has expired."),
        MockInvoice("in_demo_004", "peter@example.de", 1299, "try_again", "Your bank is temporarily unavailable."),
    ]


def print_diagnostic_report(failed_invoices):
    """Print a comprehensive failure analysis and retry recommendations."""
    
    print("=" * 70)
    print("  SUBSCRIPTION INVOICE FAILURE DIAGNOSTIC")
    print("  Audible Books GmbH (Vienna)")
    print("=" * 70)
    
    if not failed_invoices:
        print("\n  ✓ No failed invoices found. All subscriptions are healthy.")
        print("=" * 70)
        return
    
    # Classify all failures
    breakdown = {
        "TEMPORARY": [],
        "PERMANENT": [],
        "ACTION_REQUIRED": [],
        "UNKNOWN": [],
    }
    
    for inv in failed_invoices:
        category, code = classify_failure(inv)
        breakdown[category].append((inv, code))
    
    # Print summary
    total = len(failed_invoices)
    print(f"\n  Total failed invoices: {total}")
    print(f"  • Temporary (can retry):   {len(breakdown['TEMPORARY'])}")
    print(f"  • Permanent (need action): {len(breakdown['PERMANENT'])}")
    print(f"  • Action required:         {len(breakdown['ACTION_REQUIRED'])}")
    print(f"  • Unknown:                 {len(breakdown['UNKNOWN'])}")
    
    # Print detailed breakdown
    print("\n" + "=" * 70)
    print("  BREAKDOWN BY FAILURE REASON")
    print("=" * 70)
    
    for category, invs in breakdown.items():
        if invs:
            print(f"\n  [{category}]")
            for inv, code in invs:
                error_msg = inv.last_finalization_error.get("message", "Unknown error")
                print(f"    • {inv.id} — {code}")
                print(f"      Customer: {inv.customer_email or inv.customer}")
                print(f"      Amount: {inv.amount_due / 100:.2f} {inv.currency.upper()}")
                print(f"      Error: {error_msg}")
                
                # Retry recommendation
                if category == "TEMPORARY":
                    print(f"      ✓ RETRY: Safe to retry immediately")
                elif category == "ACTION_REQUIRED":
                    print(f"      ⚠️  ACTION: Customer must complete 3DS or similar")
                elif category == "PERMANENT":
                    failure_guidance = PERMANENT_FAILURES.get(code, "Contact customer")
                    print(f"      ✗ NO RETRY: {failure_guidance}")
                else:
                    print(f"      ? UNKNOWN: Investigate and retry manually")
    
    # Print recommendations
    print("\n" + "=" * 70)
    print("  RECOMMENDATIONS")
    print("=" * 70)
    
    if breakdown["TEMPORARY"]:
        print(f"\n  1. RETRY TEMPORARY FAILURES ({len(breakdown['TEMPORARY'])} invoices)")
        print("     → These are safe to retry immediately.")
        print("     → Use exponential backoff: 1 sec, 2 sec, 4 sec between retries.")
        print("     → Max 3 retries per invoice.")
    
    if breakdown["PERMANENT"]:
        print(f"\n  2. NOTIFY CUSTOMERS OF PERMANENT FAILURES ({len(breakdown['PERMANENT'])} invoices)")
        print("     → Send email asking them to update their payment method.")
        print("     → Link to billing dashboard or payment update form.")
        print("     → Example: 'Your subscription payment failed because your card")
        print("       was declined. Please update your card details to reactivate.")
        print("       No charges will be applied until you update.'")
    
    if breakdown["ACTION_REQUIRED"]:
        print(f"\n  3. TRIGGER 3D SECURE OR PAYMENT ACTION ({len(breakdown['ACTION_REQUIRED'])} invoices)")
        print("     → Customer must authenticate payment via 3D Secure.")
        print("     → Send email: 'Your payment needs verification. Please complete")
        print("       the authentication on your billing page.'")
    
    print("\n" + "=" * 70)
    print("  AUTOMATION STRATEGY")
    print("=" * 70)
    print("\n  Listen to webhook: invoice.payment_failed")
    print("  → Immediately retry temporary failures (1 sec delay)")
    print("  → After 1 hour, retry again if still temporary")
    print("  → After 6 hours, notify customer of permanent failure")
    print("  → Never retry permanent failures (wastes API calls)")
    print("\n  Listen to webhook: invoice.payment_action_required")
    print("  → Email customer with authentication link")
    print("  → Retry after customer completes action")
    print("=" * 70)


if __name__ == "__main__":
    print("Fetching failed invoices...\n")
    failed_invoices = fetch_failed_invoices(limit=50)
    
    # If no real invoices found, use demo data
    if not failed_invoices:
        print("(No failed invoices in test account — using demo data)\n")
        failed_invoices = get_demo_failed_invoices()
    
    print_diagnostic_report(failed_invoices)
