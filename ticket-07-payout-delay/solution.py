"""
Ticket 07 — Payout Delay Root-Cause Investigation
Diagnose why payouts have stopped and identify the root cause.
"""

import os
import stripe
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def fetch_recent_payouts(limit=10):
    """Fetch recent payout attempts to see status and timing."""
    payouts_list = stripe.Payout.list(limit=limit)
    return list(payouts_list.auto_paging_iter())


def check_account_restrictions():
    """Check if account has holds, restrictions, or verification issues."""
    account = stripe.Account.retrieve()
    
    restrictions = {
        "charges_enabled": account.charges_enabled,
        "payouts_enabled": account.payouts_enabled,
        "requirements": account.get("requirements", {}),
        "disabled_reason": account.get("disabled_reason"),
    }
    
    return restrictions, account


def fetch_balance():
    """Get current balance breakdown."""
    balance = stripe.Balance.retrieve()
    return balance


def fetch_bank_account_verification():
    """Check the external account (bank) verification status."""
    try:
        account = stripe.Account.retrieve()
        external_accounts = account.external_accounts.data if account.external_accounts else []
        
        if external_accounts:
            return external_accounts[0]  # Return first (primary) account
        else:
            return None
    except:
        return None


def fetch_balance_transactions(limit=50):
    """Fetch recent balance transactions to understand money flow."""
    transactions = stripe.BalanceTransaction.list(limit=limit)
    return list(transactions.auto_paging_iter())


def analyze_payout_history(payouts_list):
    """Analyze payout patterns to find when they stopped."""
    if not payouts_list:
        return None, None
    
    # Find last successful payout
    last_success = None
    first_failure = None
    
    for payout in payouts_list:
        if payout.status == "paid":
            if not last_success:
                last_success = payout
        elif payout.status in ["failed", "canceled"]:
            if not first_failure:
                first_failure = payout
    
    return last_success, first_failure


def get_demo_payouts():
    """Return mock payouts matching the SwiftShop scenario."""
    class MockPayout:
        def __init__(self, payout_id, amount, status, failure_code, created_ts):
            self.id = payout_id
            self.amount = amount
            self.status = status
            self.failure_code = failure_code
            self.created = created_ts
    
    now = int(time.time())
    
    return [
        # Last successful payout (3 days ago)
        MockPayout("po_demo_001", 18500, "paid", None, now - (3600 * 72) - 7200),
        
        # Failed attempts since then
        MockPayout("po_demo_002", 19200, "failed", "account_closed", now - (3600 * 48)),
        MockPayout("po_demo_003", 19200, "failed", "account_closed", now - (3600 * 24)),
        MockPayout("po_demo_004", 19200, "failed", "account_closed", now - (3600 * 12)),
        MockPayout("po_demo_005", 19200, "failed", "account_closed", now - 3600),
    ]


def print_diagnostic_report(payouts_list, restrictions, balance, bank_account, transactions):
    """Print comprehensive payout delay diagnostic."""
    
    print("=" * 70)
    print("  PAYOUT DELAY ROOT-CAUSE INVESTIGATION")
    print("  SwiftShop GmbH (Munich)")
    print("=" * 70)
    
    # Section 1: Account Status
    print("\n" + "=" * 70)
    print("  ACCOUNT STATUS")
    print("=" * 70)
    
    charges = "✓ ENABLED" if restrictions["charges_enabled"] else "✗ DISABLED"
    payouts_status = "✓ ENABLED" if restrictions["payouts_enabled"] else "✗ DISABLED"
    
    print(f"\n  Charges:     {charges}")
    print(f"  Payouts:     {payouts_status}")
    
    if restrictions["disabled_reason"]:
        print(f"  Disabled:    {restrictions['disabled_reason']}")
    
    # Check for requirements
    reqs = restrictions.get("requirements", {})
    if reqs.get("currently_due"):
        print(f"\n  ⚠️  REQUIREMENTS BLOCKING PAYOUTS:")
        for req in reqs["currently_due"][:5]:
            print(f"    - {req}")
        if len(reqs["currently_due"]) > 5:
            print(f"    ... and {len(reqs['currently_due']) - 5} more")
    
    # Section 2: Recent Payouts
    print("\n" + "=" * 70)
    print("  RECENT PAYOUT ATTEMPTS (Last 10)")
    print("=" * 70)
    
    if not payouts_list:
        print("\n  No payouts found.")
    else:
        for i, payout in enumerate(payouts_list[:10], 1):
            status_icon = "✓" if payout.status == "paid" else "✗" if payout.status == "failed" else "⏳"
            created = datetime.fromtimestamp(payout.created).strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n  {i}. {payout.id}")
            print(f"     Status:     {payout.status.upper()} {status_icon}")
            print(f"     Amount:     {payout.amount / 100:.2f} EUR")
            print(f"     Created:    {created}")
            
            if payout.failure_code:
                print(f"     Failure:    {payout.failure_code}")
    
    # Find patterns
    last_success, first_failure = analyze_payout_history(payouts_list)
    
    if last_success and first_failure:
        last_ts = datetime.fromtimestamp(last_success.created)
        first_ts = datetime.fromtimestamp(first_failure.created)
        gap = first_ts - last_ts
        
        print(f"\n  Last successful payout: {last_success.id} on {last_ts.strftime('%Y-%m-%d at %H:%M')}")
        print(f"  First failed payout:    {first_failure.id} on {first_ts.strftime('%Y-%m-%d at %H:%M')}")
        print(f"  Gap between:            {gap.days} day(s), {gap.seconds // 3600} hours")
    
    # Section 3: Balance
    print("\n" + "=" * 70)
    print("  CURRENT BALANCE")
    print("=" * 70)
    
    available = balance.get("available", [])
    pending = balance.get("pending", [])
    
    total_available = sum(b["amount"] for b in available) / 100
    total_pending = sum(b["amount"] for b in pending) / 100
    
    print(f"\n  Available:  €{total_available:.2f}")
    print(f"  Pending:    €{total_pending:.2f}")
    print(f"  Total:      €{(total_available + total_pending):.2f}")
    
    if total_pending > 5000:
        print(f"\n  ⚠️  Large pending balance ({total_pending:.2f} EUR)")
        print(f"      This suggests payouts aren't being sent out.")
    
    # Section 4: Bank Account
    print("\n" + "=" * 70)
    print("  BANK ACCOUNT VERIFICATION")
    print("=" * 70)
    
    if bank_account:
        print(f"\n  Account:     {bank_account.get('display_name', 'N/A')}")
        print(f"  Last 4:      {bank_account.get('last4', 'N/A')}")
        print(f"  Bank Name:   {bank_account.get('bank_name', 'N/A')}")
        print(f"  Status:      {bank_account.get('status', 'N/A')}")
        
        if bank_account.get("status") != "verified":
            print(f"\n  ⚠️  Bank account is NOT verified!")
            print(f"      This is likely blocking payouts.")
    else:
        print("\n  ✗ No external bank account configured!")
        print("     Payouts cannot be sent without a bank account.")
    
    # Section 5: Recommendations
    print("\n" + "=" * 70)
    print("  ROOT-CAUSE ANALYSIS & RECOMMENDATIONS")
    print("=" * 70)
    
    issues = []
    
    # Check each potential issue
    if not restrictions["payouts_enabled"]:
        issues.append(("CRITICAL", "Payouts disabled on account", 
                      "Account has been restricted. Contact Stripe support immediately."))
    
    if reqs.get("currently_due"):
        issues.append(("CRITICAL", f"{len(reqs['currently_due'])} missing requirements",
                      "Complete identity verification in Stripe Dashboard."))
    
    if bank_account and bank_account.get("status") != "verified":
        issues.append(("CRITICAL", "Bank account not verified",
                      "Verify bank account details in Dashboard → Settings → Bank Account."))
    
    if total_pending > total_available:
        issues.append(("WARNING", "More pending than available",
                      "System may be blocking payouts due to pending disputes/chargebacks."))
    
    if first_failure and (datetime.now() - datetime.fromtimestamp(first_failure.created)).days >= 2:
        issues.append(("WARNING", "Payouts failing for 2+ days",
                      "Systematic issue — not a one-time glitch."))
    
    if not issues:
        print("\n  ✓ No obvious blocking issues found.")
        print("    This may be a temporary Stripe processing delay.")
        print("    Recommended action: Monitor for next 6 hours, then contact Stripe if continues.")
    else:
        for severity, issue, action in issues:
            print(f"\n  [{severity}] {issue}")
            print(f"  → Action: {action}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("Investigating payout delays...\n")
    
    payouts_list = fetch_recent_payouts(limit=10)
    
    # If no real payouts, use demo data
    if not payouts_list:
        print("(No real payouts in test account — using demo data)\n")
        payouts_list = get_demo_payouts()
    
    restrictions, account = check_account_restrictions()
    balance = fetch_balance()
    bank_account = fetch_bank_account_verification()
    transactions = fetch_balance_transactions(limit=50)
    
    print_diagnostic_report(payouts_list, restrictions, balance, bank_account, transactions)
