"""
Ticket 05 — Connect Platform: Connected Account Onboarding
Account: Markethub GmbH (Berlin)
TAM Solution: List connected accounts, surface blocking requirements,
generate onboarding links for incomplete accounts.
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# =============================================================================
# PART 1 — CONNECT ACCOUNT TYPES (for reference)
# =============================================================================
#
# EXPRESS  — Stripe hosts the onboarding UI and dashboard. Seller sees Stripe.
#            Fastest to integrate. Most common for marketplaces.
#            Markethub is using this.
#
# STANDARD — Seller connects their existing Stripe account. Full Stripe access.
#            Good for platforms with sophisticated sellers (e.g. SaaS tools).
#
# CUSTOM   — Platform controls everything — UI, dashboard, payouts.
#            Most flexible but most compliance burden falls on the platform.
#            Requires deepest integration effort.
#
# CHARGES_ENABLED  — the account can accept payments from buyers
# PAYOUTS_ENABLED  — the account can receive payouts to their bank
#
# Both must be true for a seller to be fully operational.
# =============================================================================


def list_connected_accounts():
    """
    List all connected accounts and their onboarding status.
    Shows what's blocking charges or payouts for each seller.
    """
    print("=" * 60)
    print("CONNECTED ACCOUNT STATUS — Markethub GmbH")
    print("=" * 60)

    accounts = stripe.Account.list(limit=20)

    if not accounts.data:
        print("\nNo connected accounts found.")
        print("Create a test connected account with:")
        print("  See Part 3 below — create_test_connected_account()")
        return []

    for account in accounts.auto_paging_iter():
        charges_ok = account.get("charges_enabled", False)
        payouts_ok = account.get("payouts_enabled", False)
        reqs = account.get("requirements", {})
        currently_due = reqs.get("currently_due", [])
        disabled_reason = reqs.get("disabled_reason", None)

        status = "✓ FULLY ACTIVE" if (charges_ok and payouts_ok) else "⚠ RESTRICTED"

        print(f"\n  Account ID   : {account['id']}")
        print(f"  Email        : {account.get('email', 'n/a')}")
        print(f"  Status       : {status}")
        print(f"  Charges      : {'enabled' if charges_ok else 'DISABLED'}")
        print(f"  Payouts      : {'enabled' if payouts_ok else 'DISABLED'}")

        if disabled_reason:
            print(f"  Blocked by   : {disabled_reason}")

        if currently_due:
            print(f"  Currently due ({len(currently_due)} fields):")
            for field in currently_due:
                print(f"    - {field}")
        else:
            print(f"  Currently due: none")

    return accounts.data


def create_test_connected_account():
    """
    Create a test Express connected account.
    In production, your platform creates these when a seller signs up.
    """
    print("\n" + "=" * 60)
    print("CREATING TEST CONNECTED ACCOUNT")
    print("=" * 60)

    account = stripe.Account.create(
        type="express",
        country="DE",
        email="seller-test@markethub.example.com",
        capabilities={
            "card_payments": {"requested": True},
            "transfers": {"requested": True},
        },
    )

    print(f"  Created account : {account['id']}")
    print(f"  Type            : {account['type']}")
    print(f"  Country         : {account['country']}")
    print(f"  Charges enabled : {account['charges_enabled']}")
    print(f"  Payouts enabled : {account['payouts_enabled']}")
    print(f"  Status          : restricted (onboarding not complete)")

    return account["id"]


def create_onboarding_link(account_id):
    """
    Generate a fresh onboarding link for a seller who hasn't completed setup.
    Send this URL to the seller — it opens Stripe's hosted onboarding flow.
    Links expire after a short time, so always generate a new one on demand.
    """
    print(f"\n{'=' * 60}")
    print(f"ONBOARDING LINK — {account_id}")
    print("=" * 60)

    link = stripe.AccountLink.create(
        account=account_id,
        refresh_url="https://markethub.example.com/onboarding/refresh",
        return_url="https://markethub.example.com/onboarding/complete",
        type="account_onboarding",
    )

    print(f"  Onboarding URL : {link['url']}")
    print(f"  Expires at     : {link['expires_at']}")
    print(f"\n  → Send this URL to the seller.")
    print(f"  → It opens Stripe's hosted KYC/onboarding form.")
    print(f"  → Once complete, Stripe fires account.updated webhook.")
    print(f"  → Listen for charges_enabled = true to mark them as active.")


# =============================================================================
# PART 4 — WEBHOOK: account.updated
# =============================================================================
#
# Add this event to your webhook endpoint to track seller verification:
#
#   elif event_type == "account.updated":
#       account = event["data"]["object"]
#       if account["charges_enabled"] and account["payouts_enabled"]:
#           # Seller is fully verified — activate their storefront
#           activate_seller(account["id"])
#       elif account["requirements"]["currently_due"]:
#           # Seller still has outstanding requirements — send reminder
#           send_reminder_email(account["id"], account["requirements"])
#
# This is what Markethub is missing — without this webhook, they have no
# way to know when a seller finishes onboarding or what's still blocking them.
# =============================================================================


def explain_webhook_strategy():
    print("\n" + "=" * 60)
    print("WEBHOOK STRATEGY — account.updated")
    print("=" * 60)
    print("""
  Markethub is not listening to account.updated.
  This is why they have no visibility into seller verification.

  What to listen for:
    charges_enabled → true   : seller can now accept payments
    payouts_enabled → true   : seller can now receive payouts
    requirements.currently_due not empty : action still needed

  Recommended flow:
    1. Seller signs up → platform calls stripe.Account.create()
    2. Platform sends seller the AccountLink onboarding URL
    3. Seller completes Stripe's KYC form
    4. Stripe fires account.updated
    5. Platform checks charges_enabled + payouts_enabled
    6. If both true → activate seller storefront
    7. If requirements still due → email seller with what's needed

  Never poll the Account object on a schedule.
  Use the webhook — it fires immediately when status changes.
""")


if __name__ == "__main__":
    print("\nTicket 05 — Connect Platform: Connected Account Onboarding")
    print("Account: Markethub GmbH (Berlin)\n")

    # Step 1: Show all connected accounts and what's blocking them
    accounts = list_connected_accounts()

    # Step 2: If no accounts exist, create a test one
    if not accounts:
        account_id = create_test_connected_account()
        # Step 3: Generate onboarding link for the new account
        create_onboarding_link(account_id)
    else:
        # Generate a fresh onboarding link for the first restricted account
        restricted = [
            a for a in accounts
            if not a.get("charges_enabled") or not a.get("payouts_enabled")
        ]
        if restricted:
            create_onboarding_link(restricted[0]["id"])

    # Step 4: Explain the webhook strategy
    explain_webhook_strategy()
