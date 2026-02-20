"""
Ticket 02 — Webhook Debugging & Event Verification
Secure Flask webhook receiver with signature verification
and missed event recovery via the Stripe Events API.
"""

import os
import stripe
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

app = Flask(__name__)


# ─── WEBHOOK RECEIVER ─────────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    # Step 1 — Verify the signature
    # Without this, anyone can send fake events to your endpoint.
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        print("⚠️  Invalid signature — request rejected.")
        return jsonify({"error": "Invalid signature"}), 400

    # Step 2 — Route to the correct handler
    event_type = event["type"]
    data = event["data"]["object"]

    handlers = {
        "payment_intent.succeeded":      handle_payment_succeeded,
        "payment_intent.payment_failed": handle_payment_failed,
        "charge.dispute.created":        handle_dispute_created,
    }

    handler = handlers.get(event_type)
    if handler:
        handler(data)
    else:
        print(f"Unhandled event type: {event_type}")

    # Always return 200 quickly — Stripe will retry if you don't
    return jsonify({"status": "ok"}), 200


def handle_payment_succeeded(payment_intent):
    print(f"✓ Payment succeeded: {payment_intent['id']}")
    print(f"  Amount: {payment_intent['amount'] / 100:.2f} {payment_intent['currency'].upper()}")
    print(f"  → Fulfil order for customer: {payment_intent.get('customer', 'guest')}")


def handle_payment_failed(payment_intent):
    error = payment_intent.get("last_payment_error", {})
    print(f"✗ Payment failed: {payment_intent['id']}")
    print(f"  Reason: {error.get('decline_code') or error.get('code', 'unknown')}")
    print(f"  → Notify customer and prompt retry")


def handle_dispute_created(charge):
    print(f"⚠️  Dispute opened on charge: {charge['id']}")
    print(f"  Amount: {charge['amount'] / 100:.2f}")
    print(f"  → Gather evidence immediately — deadline is 7-21 days")


# ─── MISSED EVENT RECOVERY ────────────────────────────────────────────────────

def fetch_missed_events(hours_ago=72):
    """
    Fetch events from the last N hours via the Stripe Events API.
    Use this to recover events your server missed while it was down.
    """
    import time
    since = int(time.time()) - (hours_ago * 3600)

    print(f"\nFetching events from the last {hours_ago} hours...\n")

    events = stripe.Event.list(
        created={"gte": since},
        types=["payment_intent.succeeded", "payment_intent.payment_failed"],
        limit=50,
    )

    for event in events.auto_paging_iter():
        obj = event["data"]["object"]
        print(f"  [{event['type']}] {event['id']} — {obj.get('id', 'n/a')}")

    print("\nDone. Replay any missed events using:")
    print("  stripe events resend <event_id>")


if __name__ == "__main__":
    print("Starting webhook receiver on http://localhost:4242/webhook")
    print("In a second terminal run:")
    print("  stripe listen --forward-to localhost:4242/webhook\n")
    fetch_missed_events(hours_ago=72)
    app.run(port=4242)
