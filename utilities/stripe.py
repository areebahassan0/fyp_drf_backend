# utils/stripe_utils.py
import stripe
from django.conf import settings
import os

# Debug prints
print("Checking Stripe configuration...")
print(f"STRIPE_SECRET_KEY from settings: {settings.STRIPE_SECRET_KEY[:10]}..." if settings.STRIPE_SECRET_KEY else "No STRIPE_SECRET_KEY found")

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_payment_intent(amount, currency='usd', metadata={}):
    try:
        if not stripe.api_key:
            raise Exception("Stripe API key is not configured. Please check your .env file and settings.py")
            
        print(f"Creating payment intent for amount: {amount}")
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses the smallest currency unit
            currency=currency,
            metadata=metadata
        )
        print(f"Payment intent created successfully: {intent.id}")
        return intent
        
    except stripe.error.AuthenticationError as e:
        print(f"Stripe authentication error: {str(e)}")
        raise Exception("Stripe API key is invalid. Please check your .env file and settings.py")
    except Exception as e:
        print(f"Stripe error: {str(e)}")
        raise Exception(f"Stripe error: {str(e)}")
