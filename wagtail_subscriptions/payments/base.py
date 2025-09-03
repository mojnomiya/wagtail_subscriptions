from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.conf import settings


class BasePaymentProcessor(ABC):
    """Abstract base class for payment processors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup()
    
    @abstractmethod
    def setup(self):
        """Initialize the payment processor with configuration"""
        pass
    
    @abstractmethod
    def create_customer(self, user, **kwargs) -> str:
        """Create a customer in the payment processor and return external ID"""
        pass
    
    @abstractmethod
    def create_subscription(self, customer_id: str, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Create a subscription and return subscription data"""
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel a subscription"""
        pass
    
    @abstractmethod
    def update_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Update a subscription (change plan, etc.)"""
        pass
    
    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve subscription details"""
        pass
    
    @abstractmethod
    def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process webhook payload and return event data"""
        pass
    
    @abstractmethod
    def create_payment_method(self, customer_id: str, payment_method_data: Dict[str, Any]) -> str:
        """Create a payment method and return external ID"""
        pass
    
    @abstractmethod
    def charge_customer(self, customer_id: str, amount: float, currency: str = 'USD', **kwargs) -> Dict[str, Any]:
        """Charge a customer and return payment data"""
        pass


def get_payment_processor(processor_name: str = None) -> BasePaymentProcessor:
    """Factory function to get payment processor instance"""
    if not processor_name:
        processor_name = getattr(settings, 'WAGTAIL_SUBSCRIPTIONS_DEFAULT_PROCESSOR', 'stripe')
    
    config = getattr(settings, 'WAGTAIL_SUBSCRIPTIONS', {}).get('PAYMENT_PROCESSORS', {}).get(processor_name, {})
    
    if processor_name == 'stripe':
        from .stripe import StripePaymentProcessor
        return StripePaymentProcessor(config)
    elif processor_name == 'paddle':
        from .paddle import PaddlePaymentProcessor
        return PaddlePaymentProcessor(config)
    elif processor_name == 'paypal':
        from .paypal import PayPalPaymentProcessor
        return PayPalPaymentProcessor(config)
    else:
        raise ValueError(f"Unsupported payment processor: {processor_name}")