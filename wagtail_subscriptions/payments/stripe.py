import stripe
from typing import Dict, Any
from django.conf import settings
from .base import BasePaymentProcessor


class StripePaymentProcessor(BasePaymentProcessor):
    """Stripe payment processor implementation"""
    
    def setup(self):
        """Initialize Stripe with API keys"""
        stripe.api_key = self.config.get('secret_key')
        self.webhook_secret = self.config.get('webhook_secret')
    
    def create_customer(self, user, **kwargs) -> str:
        """Create a Stripe customer"""
        customer_data = {
            'email': user.email,
            'name': user.get_full_name() or user.username,
            'metadata': {
                'user_id': str(user.id),
            }
        }
        customer_data.update(kwargs)
        
        customer = stripe.Customer.create(**customer_data)
        return customer.id
    
    def create_subscription(self, customer_id: str, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Create a Stripe subscription"""
        subscription_data = {
            'customer': customer_id,
            'items': [{'price': plan_id}],
            'expand': ['latest_invoice.payment_intent'],
        }
        subscription_data.update(kwargs)
        
        subscription = stripe.Subscription.create(**subscription_data)
        
        return {
            'id': subscription.id,
            'status': subscription.status,
            'current_period_start': subscription.current_period_start,
            'current_period_end': subscription.current_period_end,
            'trial_end': subscription.trial_end,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice.payment_intent else None,
        }
    
    def cancel_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel a Stripe subscription"""
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=kwargs.get('at_period_end', True)
        )
        
        return {
            'id': subscription.id,
            'status': subscription.status,
            'canceled_at': subscription.canceled_at,
            'cancel_at_period_end': subscription.cancel_at_period_end,
        }
    
    def update_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Update a Stripe subscription"""
        subscription = stripe.Subscription.modify(subscription_id, **kwargs)
        
        return {
            'id': subscription.id,
            'status': subscription.status,
            'current_period_start': subscription.current_period_start,
            'current_period_end': subscription.current_period_end,
        }
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve Stripe subscription details"""
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        return {
            'id': subscription.id,
            'status': subscription.status,
            'current_period_start': subscription.current_period_start,
            'current_period_end': subscription.current_period_end,
            'trial_end': subscription.trial_end,
            'canceled_at': subscription.canceled_at,
        }
    
    def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process Stripe webhook"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return {
                'id': event['id'],
                'type': event['type'],
                'data': event['data'],
                'created': event['created'],
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
    
    def charge_customer(self, customer_id: str, amount: float, currency: str = 'USD', **kwargs) -> Dict[str, Any]:
        """Charge a Stripe customer"""
        charge_data = {
            'amount': int(amount * 100),  # Convert to cents
            'currency': currency.lower(),
            'customer': customer_id,
        }
        charge_data.update(kwargs)
        
        payment_intent = stripe.PaymentIntent.create(**charge_data)
        
        return {
            'id': payment_intent.id,
            'status': payment_intent.status,
            'amount': payment_intent.amount / 100,  # Convert back to dollars
            'currency': payment_intent.currency,
            'client_secret': payment_intent.client_secret,
        }