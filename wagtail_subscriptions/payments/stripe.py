from typing import Any, Dict

import stripe

from .base import BasePaymentProcessor


class StripePaymentProcessor(BasePaymentProcessor):
    """Stripe payment processor implementation"""

    def setup(self):
        """Initialize Stripe with API keys"""
        stripe.api_key = self.config.get("secret_key")
        self.webhook_secret = self.config.get("webhook_secret")
        self.validate_config(["secret_key", "webhook_secret"])

    def create_customer(self, user_or_email, **kwargs) -> Dict[str, Any]:
        """Create a Stripe customer

        Args:
            user_or_email: User object or email string
        """
        if isinstance(user_or_email, str):
            # Email string provided
            customer_data = {
                "email": user_or_email,
                "metadata": kwargs.get("metadata", {}),
            }
        else:
            # User object provided
            customer_data = {
                "email": user_or_email.email,
                "name": user_or_email.get_full_name() or user_or_email.username,
                "metadata": {
                    "user_id": str(user_or_email.id),
                },
            }
        customer_data.update(kwargs)

        customer = stripe.Customer.create(**customer_data)
        return {"id": customer.id, "email": customer.email}

    def create_subscription(self, customer_id: str, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Create a Stripe subscription"""
        subscription_data = {
            "customer": customer_id,
            "items": [{"price": plan_id}],
            "expand": ["latest_invoice.payment_intent"],
        }
        subscription_data.update(kwargs)

        subscription = stripe.Subscription.create(**subscription_data)

        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "trial_end": subscription.trial_end,
            "client_secret": (
                subscription.latest_invoice.payment_intent.client_secret
                if subscription.latest_invoice.payment_intent
                else None
            ),
        }

    def cancel_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel a Stripe subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id, cancel_at_period_end=kwargs.get("at_period_end", True)
            )

            return {
                "id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at,
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {e.user_message}")

    def update_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Update a Stripe subscription"""
        try:
            subscription = stripe.Subscription.modify(subscription_id, **kwargs)

            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {e.user_message}")

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve Stripe subscription details"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_end": subscription.trial_end,
                "canceled_at": subscription.canceled_at,
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {e.user_message}")

    def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process Stripe webhook"""
        try:
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return {
                "id": event["id"],
                "type": event["type"],
                "data": event["data"],
                "created": event["created"],
            }
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")

    def create_payment_method(self, customer_id: str, payment_method_data: Dict[str, Any]) -> str:
        """Create a Stripe payment method"""
        payment_method = stripe.PaymentMethod.create(**payment_method_data)

        # Attach to customer
        payment_method.attach(customer=customer_id)

        return payment_method.id

    def charge_customer(
        self, customer_id: str, amount: float, currency: str = "USD", **kwargs
    ) -> Dict[str, Any]:
        """Charge a Stripe customer"""
        charge_data = {
            "amount": int(amount * 100),  # Convert to cents
            "currency": currency.lower(),
            "customer": customer_id,
        }
        charge_data.update(kwargs)

        payment_intent = stripe.PaymentIntent.create(**charge_data)

        return {
            "id": payment_intent.id,
            "status": payment_intent.status,
            "amount": payment_intent.amount / 100,  # Convert back to dollars
            "currency": payment_intent.currency,
            "client_secret": payment_intent.client_secret,
        }
