"""
Ticket 08 — SCA / 3D Secure for PSD2 Compliance
Demonstrate how PaymentIntents handle Strong Customer Authentication (3DS).
"""

import os
import stripe
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def create_payment_intent_with_3ds(amount, currency="eur", description="3DS Test"):
    """Create a PaymentIntent that will trigger 3D Secure."""
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        description=description,
        payment_method_types=["card"],
    )
    return intent


def confirm_payment_with_test_card(intent_id, test_card="4000002500003010"):
    """
    Confirm the PaymentIntent with a test card that requires 3DS.
    
    Test cards:
    - 4000002500003010 (Requires 3DS) ← Most common for testing
    - 4000000000003220 (Requires 3DS with redirect)
    - 4242424242424242 (No 3DS required)
    """
    try:
        intent = stripe.PaymentIntent.confirm(
            intent_id,
            payment_method={
                "type": "card",
                "card": {
                    "number": test_card,
                    "exp_month": 12,
                    "exp_year": 2026,
                    "cvc": "314",
                },
            },
            return_url="https://example.com/checkout/complete",
        )
        return intent
    except stripe.error.CardError as e:
        return None, e


def get_demo_3ds_flow():
    """
    Demonstrate a realistic 3DS flow showing both successful and failed authentication.
    """
    demo = {
        "successful_3ds": {
            "intent_id": "pi_demo_3ds_success",
            "amount": 2999,
            "status": "requires_action",
            "action_required": {
                "type": "use_stripe_sdk",
                "use_stripe_sdk": {
                    "stripe_js": "https://js.stripe.com/v3",
                    "client_secret": "pi_demo_3ds_success_secret_AbCdEfGhIjKlMnOp"
                }
            },
            "client_secret": "pi_demo_3ds_success_secret_AbCdEfGhIjKlMnOp",
            "flow": [
                "1. Customer enters card: 4000002500003010",
                "2. PaymentIntent.confirm() → Status: requires_action",
                "3. Frontend detects requires_action",
                "4. Call stripe.confirmCardPayment(clientSecret)",
                "5. 3DS iframe appears → Customer enters OTP",
                "6. Webhook: payment_intent.payment_action_required fires",
                "7. Customer completes authentication",
                "8. Webhook: payment_intent.succeeded fires",
                "9. Payment complete ✓"
            ]
        },
        "failed_3ds": {
            "intent_id": "pi_demo_3ds_failed",
            "amount": 1999,
            "status": "requires_action",
            "action_required": "3DS challenge",
            "flow": [
                "1. Customer enters card: 4000002500003010",
                "2. PaymentIntent.confirm() → Status: requires_action",
                "3. Frontend detects requires_action",
                "4. Call stripe.confirmCardPayment(clientSecret)",
                "5. 3DS iframe appears",
                "6. Customer fails authentication (wrong OTP)",
                "7. Webhook: payment_intent.payment_action_required fires",
                "8. Payment marked as failed ✗",
                "9. Frontend shows retry button"
            ]
        }
    }
    return demo


def print_psd2_compliance_guide():
    """Print a comprehensive PSD2/3DS implementation guide."""
    
    print("=" * 70)
    print("  PSD2 / SCA / 3D SECURE IMPLEMENTATION GUIDE")
    print("  TechnoShop GmbH (Berlin)")
    print("=" * 70)
    
    # Section 1: What is PSD2?
    print("\n" + "=" * 70)
    print("  WHAT IS PSD2 AND STRONG CUSTOMER AUTHENTICATION (SCA)?")
    print("=" * 70)
    
    print("""
  PSD2 (Payment Services Directive 2) is an EU regulation requiring
  Strong Customer Authentication (SCA) for online card payments.
  
  In plain English:
  → Customers must PROVE their identity during checkout
  → Methods: password + SMS code, biometric (fingerprint), etc.
  → Technical implementation: 3D Secure (3DS)
  
  What this means for your integration:
  ✓ Stripe handles 3DS automatically with PaymentIntent
  ✓ No additional setup required in most cases
  ✓ Your checkout flow detects when 3DS is needed
  ✓ Customer sees a secure authentication popup
  ✓ Payment completes after successful authentication
    """)
    
    # Section 2: How Stripe Handles 3DS
    print("\n" + "=" * 70)
    print("  HOW STRIPE AUTOMATICALLY HANDLES 3D SECURE")
    print("=" * 70)
    
    print("""
  Your current flow:
  1. Customer enters card details
  2. stripe.confirmCardPayment(clientSecret)
  3. Stripe returns status
  
  When 3DS is required, Stripe automatically:
  ✓ Detects the card needs authentication
  ✓ Returns status: 'requires_action'
  ✓ Provides the 3DS authentication URL
  
  Frontend detects requires_action and:
  ✓ Shows the 3DS challenge iframe to customer
  ✓ Customer completes authentication
  ✓ Payment automatically transitions to 'succeeded'
    """)
    
    # Section 3: Test Flow
    print("\n" + "=" * 70)
    print("  TEST 3DS FLOW EXAMPLE")
    print("=" * 70)
    
    demo = get_demo_3ds_flow()
    
    print("\n  [SUCCESSFUL 3DS FLOW]")
    print(f"  Intent ID: {demo['successful_3ds']['intent_id']}")
    print(f"  Amount: €{demo['successful_3ds']['amount']/100:.2f}")
    print(f"  Status: {demo['successful_3ds']['status']}")
    print(f"\n  Steps:")
    for step in demo['successful_3ds']['flow']:
        print(f"    {step}")
    
    print("\n  [FAILED 3DS FLOW]")
    print(f"  Intent ID: {demo['failed_3ds']['intent_id']}")
    print(f"  Amount: €{demo['failed_3ds']['amount']/100:.2f}")
    print(f"  Status: {demo['failed_3ds']['status']}")
    print(f"\n  Steps:")
    for step in demo['failed_3ds']['flow']:
        print(f"    {step}")
    
    # Section 4: Frontend Code Example
    print("\n" + "=" * 70)
    print("  FRONTEND CODE PATTERN (JavaScript)")
    print("=" * 70)
    
    print("""
  const stripe = Stripe('pk_test_...');
  const elements = stripe.elements();
  const cardElement = elements.create('card');
  cardElement.mount('#card-element');
  
  document.getElementById('pay').addEventListener('click', async (e) => {
    e.preventDefault();
    
    // Confirm the payment
    const { paymentIntent, error } = await stripe.confirmCardPayment(
      clientSecret,
      {
        payment_method: {
          card: cardElement,
          billing_details: { name: 'Customer Name' }
        }
      }
    );
    
    if (error) {
      console.error('Payment failed:', error);
    } else if (paymentIntent.status === 'requires_action') {
      // 3DS challenge was shown automatically
      // Stripe handles the iframe and authentication
      console.log('Waiting for 3DS...');
    } else if (paymentIntent.status === 'succeeded') {
      console.log('Payment successful!');
    }
  });
    """)
    
    # Section 5: Backend Webhook Handling
    print("\n" + "=" * 70)
    print("  BACKEND WEBHOOK HANDLING (Python)")
    print("=" * 70)
    
    print("""
  # Listen for these webhooks:
  
  @app.route('/webhook', methods=['POST'])
  def webhook():
    event = stripe.Event.construct_event(...)
    
    if event['type'] == 'payment_intent.payment_action_required':
      intent = event['data']['object']
      # 3DS authentication in progress
      print(f"3DS challenge pending for {intent['id']}")
    
    elif event['type'] == 'payment_intent.succeeded':
      intent = event['data']['object']
      # Payment is complete (3DS was successful)
      print(f"Payment successful: {intent['id']}")
      # Fulfill the order
    
    return jsonify({'status': 'ok'}), 200
    """)
    
    # Section 6: Compliance Checklist
    print("\n" + "=" * 70)
    print("  PSD2 COMPLIANCE CHECKLIST")
    print("=" * 70)
    
    checklist = [
        ("Use PaymentIntents (not Charges)", "✓ Required"),
        ("Handle 'requires_action' status", "✓ Required"),
        ("Support 3D Secure redirect", "✓ Required"),
        ("Listen to payment_intent webhooks", "✓ Required"),
        ("Validate webhook signatures", "✓ Recommended"),
        ("Test with 3DS test cards", "✓ Before go-live"),
        ("Implement error handling", "✓ Required"),
        ("Document for support team", "✓ Recommended"),
    ]
    
    for item, status in checklist:
        print(f"  ☐ {item:.<40} {status}")
    
    # Section 7: Timeline & Action
    print("\n" + "=" * 70)
    print("  YOUR ACTION PLAN")
    print("=" * 70)
    
    print("""
  This week:
    □ Review your current Stripe integration
    □ Verify you're using PaymentIntents (not Charges)
    □ Test with 3DS test card: 4000002500003010
    □ Confirm 3DS iframe appears in checkout
  
  Before go-live:
    □ Test both success and failure flows
    □ Verify webhooks are being received
    □ Update your support team documentation
    □ Notify customers about the security upgrade
  
  Result:
    ✓ PSD2 compliant
    ✓ Automatic 3DS handling
    ✓ Zero merchant burden
    ✓ Payment success rate maintained
    """)
    
    print("\n" + "=" * 70)
    print("  KEY TAKEAWAY")
    print("=" * 70)
    
    print("""
  Stripe handles 3D Secure AUTOMATICALLY with PaymentIntents.
  You don't need to build custom 3DS logic.
  
  Your job:
  1. Use PaymentIntents
  2. Handle 'requires_action' status on frontend
  3. Listen to webhooks on backend
  
  That's it. You're PSD2 compliant.
    """)
    
    print("=" * 70)


if __name__ == "__main__":
    print_psd2_compliance_guide()
