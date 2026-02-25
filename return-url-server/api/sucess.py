"""
Stripe Return URL Handler — Vercel Serverless Function
======================================================
Stripe redirects customers here after payment completion.
Reads the payment_intent and redirect_status from query params,
fetches the PaymentIntent from Stripe, and displays the result.
"""

import os
import json
import stripe
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


def build_html(title, status_emoji, status_text, details):
    """Build a clean status page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f6f9fc;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            padding: 48px;
            max-width: 480px;
            width: 100%;
            text-align: center;
        }}
        .emoji {{ font-size: 64px; margin-bottom: 16px; }}
        .status {{ font-size: 24px; font-weight: 600; color: #1a1a2e; margin-bottom: 8px; }}
        .details {{
            font-size: 14px;
            color: #6b7c93;
            line-height: 1.8;
            margin-top: 24px;
            text-align: left;
            background: #f6f9fc;
            padding: 16px;
            border-radius: 8px;
            font-family: 'SF Mono', Monaco, monospace;
        }}
        .details span {{ color: #1a1a2e; font-weight: 500; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            margin-top: 12px;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-fail {{ background: #f8d7da; color: #721c24; }}
        .badge-pending {{ background: #fff3cd; color: #856404; }}
        .footer {{
            margin-top: 32px;
            font-size: 12px;
            color: #adb5bd;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="emoji">{status_emoji}</div>
        <div class="status">{status_text}</div>
        {details}
        <div class="footer">Stripe TAM Portfolio — Return URL Server</div>
    </div>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)

        pi_id = query.get("payment_intent", [None])[0]
        redirect_status = query.get("redirect_status", ["unknown"])[0]

        # No params — show landing page
        if not pi_id:
            html = build_html(
                "Stripe Return URL",
                "🔗",
                "Return URL Server Active",
                '<p style="text-align:center;color:#6b7c93;margin-top:16px;">'
                "This endpoint receives Stripe payment redirects.<br>"
                "Add this URL as your <code>return_url</code> in PaymentIntents."
                "</p>",
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
            return

        # Fetch PaymentIntent from Stripe
        try:
            pi = stripe.PaymentIntent.retrieve(pi_id)
            amount = f"{pi.currency.upper()} {pi.amount / 100:,.2f}"
            status = pi.status

            if status == "succeeded":
                emoji, text = "✅", "Payment Succeeded"
                badge = '<span class="badge badge-success">succeeded</span>'
            elif status == "requires_payment_method":
                emoji, text = "❌", "Payment Failed"
                badge = '<span class="badge badge-fail">requires_payment_method</span>'
            else:
                emoji, text = "⏳", "Payment Processing"
                badge = f'<span class="badge badge-pending">{status}</span>'

            details = f"""
            <div>{badge}</div>
            <div class="details">
                <span>Payment Intent:</span> {pi.id}<br>
                <span>Amount:</span> {amount}<br>
                <span>Status:</span> {status}<br>
                <span>Redirect:</span> {redirect_status}<br>
                <span>Description:</span> {pi.description or "—"}
            </div>"""

            html = build_html("Payment Result", emoji, text, details)

        except stripe.error.StripeError as e:
            html = build_html(
                "Error",
                "⚠️",
                "Could not fetch payment",
                f'<p style="text-align:center;color:#e74c3c;margin-top:16px;">{str(e)}</p>',
            )

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())
