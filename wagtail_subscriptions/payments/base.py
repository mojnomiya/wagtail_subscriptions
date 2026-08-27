from abc import ABC, abstractmethod
import time
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class BasePaymentProcessor(ABC):
    """Abstract base class for payment processors"""

    # Default retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup()

    @abstractmethod
    def setup(self):
        """Initialize the payment processor with configuration"""

    @abstractmethod
    def create_customer(self, user, **kwargs) -> str:
        """Create a customer in the payment processor and return external ID"""

    @abstractmethod
    def create_subscription(self, customer_id: str, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Create a subscription and return subscription data"""

    @abstractmethod
    def cancel_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel a subscription"""

    @abstractmethod
    def update_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Update a subscription (change plan, etc.)"""

    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve subscription details"""

    @abstractmethod
    def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process webhook payload and return event data"""

    @abstractmethod
    def create_payment_method(self, customer_id: str, payment_method_data: Dict[str, Any]) -> str:
        """Create a payment method and return external ID"""

    @abstractmethod
    def charge_customer(
        self, customer_id: str, amount: float, currency: str = "USD", **kwargs
    ) -> Dict[str, Any]:
        """Charge a customer and return payment data"""

    def _make_request_with_retry(
        self, request_func, *args, **kwargs
    ) -> Any:
        """Execute a request function with retry logic"""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return request_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        raise last_exception

    def validate_config(self, required_keys: list[str]) -> None:
        """Validate that required configuration keys are present"""
        missing = [key for key in required_keys if not self.config.get(key)]
        if missing:
            raise ImproperlyConfigured(
                f"Missing required payment processor configuration: {', '.join(missing)}"
            )


# Payment processor registry
_PROCESSOR_REGISTRY = {}


def register_processor(name: str, processor_class):
    """Register a payment processor"""
    _PROCESSOR_REGISTRY[name] = processor_class


def get_registered_processors():
    """Get all registered processors"""
    return _PROCESSOR_REGISTRY.copy()


def get_payment_processor(processor_name: str = None) -> BasePaymentProcessor:
    """Factory function to get payment processor instance"""
    if not processor_name:
        processor_name = getattr(settings, "WAGTAIL_SUBSCRIPTIONS_DEFAULT_PROCESSOR", "stripe")

    config = (
        getattr(settings, "WAGTAIL_SUBSCRIPTIONS", {})
        .get("PAYMENT_PROCESSORS", {})
        .get(processor_name, {})
    )

    # Check registry first
    if processor_name in _PROCESSOR_REGISTRY:
        processor_class = _PROCESSOR_REGISTRY[processor_name]
        return processor_class(config)

    # Fallback to hardcoded processors
    if processor_name == "stripe":
        from .stripe import StripePaymentProcessor

        return StripePaymentProcessor(config)
    elif processor_name == "paddle":
        from .paddle import PaddlePaymentProcessor

        return PaddlePaymentProcessor(config)
    elif processor_name == "paypal":
        from .paypal import PayPalPaymentProcessor

        return PayPalPaymentProcessor(config)
    else:
        raise ValueError(f"Unsupported payment processor: {processor_name}")


# Auto-register built-in processors
try:
    from .stripe import StripePaymentProcessor

    register_processor("stripe", StripePaymentProcessor)
except ImportError:
    pass

try:
    from .paddle import PaddlePaymentProcessor

    register_processor("paddle", PaddlePaymentProcessor)
except ImportError:
    pass

try:
    from .paypal import PayPalPaymentProcessor

    register_processor("paypal", PayPalPaymentProcessor)
except ImportError:
    pass
