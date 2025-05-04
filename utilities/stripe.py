# utils/stripe_utils.py
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_payment_intent(amount, currency='usd', metadata={}):
    return stripe.PaymentIntent.create(
        amount=int(amount * 100),  # Stripe uses the smallest currency unit
        currency=currency,
        metadata=metadata
    )
