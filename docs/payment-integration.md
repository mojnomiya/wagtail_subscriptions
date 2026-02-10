# Payment Integration Guide

## Overview

Wagtail Subscriptions supports multiple payment processors out of the box and provides an extensible architecture for adding custom processors.

## Supported Processors

- **Stripe** - Full support with webhooks
- **Paddle** - Paddle Billing API integration
- **PayPal** - PayPal Subscriptions API

## Stripe Integration

### Setup

1. **Create Stripe Account**
   - Sign up at [stripe.com](https://stripe.com)
   - Get your API keys from the Dashboard

2. **Install Stripe SDK**
   ```bash
   pip install stripe>=5.0.0
   ```

3. **Configure Settings**
   ```python
   # settings.py
   WAGTAIL_SUBSCRIPTIONS = {
       'PAYMENT_PROCESSORS': {
           'stripe': {
               'public_key': 'pk_test_...',  # Publishable key
               'secret_key': 'sk_test_...',  # Secret key
               'webhook_secret': 'whsec_...', # Webhook signing secret
           }
       },
       'DEFAULT_PROCESSOR': 'stripe',
   }
   ```

4. **Create Products and Prices in Stripe**
   ```python
   # In Stripe Dashboard or via API
   # Create a Product: "Professional Plan"
   # Create a Price: $29.99/month
   # Copy the Price ID (e.g., price_1234567890)
   ```

5. **Link Plans to Stripe**
   ```python
   from wagtail_subscriptions.models import SubscriptionPlan
   
   plan = SubscriptionPlan.objects.create(
       name="Professional",
       slug="pro",
       price=29.99,
       billing_period="monthly",
       stripe_price_id="price_1234567890"  # From Stripe Dashboard
   )
   ```

### Webhook Configuration

1. **Add Webhook Endpoint in Stripe Dashboard**
   - URL: `https://yourdomain.com/subscriptions/webhooks/stripe/`
   - Events to listen for:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

2. **Copy Webhook Signing Secret**
   - Add to your settings as `webhook_secret`

3. **Test Webhook**
   ```bash
   # Use Stripe CLI for local testing
   stripe listen --forward-to localhost:8000/subscriptions/webhooks/stripe/
   ```

### Usage Example

```python
from wagtail_subscriptions.payments import get_payment_processor

# Get Stripe processor
processor = get_payment_processor('stripe')

# Create customer
customer = processor.create_customer(
    email='user@example.com',
    name='John Doe',
    metadata={'user_id': '123'}
)

# Create subscription
subscription = processor.create_subscription(
    customer_id=customer['id'],
    plan_id='price_1234567890',
    trial_days=14
)

# Cancel subscription
processor.cancel_subscription(
    subscription_id=subscription['id'],
    immediate=False  # Cancel at period end
)
```

### Stripe-Specific Features

#### Payment Intents

```python
# Create one-time payment
payment_intent = processor.create_payment_intent(
    amount=2999,  # $29.99 in cents
    currency='usd',
    customer_id=customer['id']
)
```

#### Payment Methods

```python
# Attach payment method
processor.attach_payment_method(
    payment_method_id='pm_1234567890',
    customer_id=customer['id']
)

# Set default payment method
processor.set_default_payment_method(
    customer_id=customer['id'],
    payment_method_id='pm_1234567890'
)
```

#### Proration

```python
# Update subscription with proration
processor.update_subscription(
    subscription_id='sub_1234567890',
    plan_id='price_new_plan',
    prorate=True
)
```

---

## Paddle Integration

### Setup

1. **Create Paddle Account**
   - Sign up at [paddle.com](https://paddle.com)
   - Get Vendor ID and Auth Code

2. **Configure Settings**
   ```python
   # settings.py
   WAGTAIL_SUBSCRIPTIONS = {
       'PAYMENT_PROCESSORS': {
           'paddle': {
               'vendor_id': '12345',
               'auth_code': 'your_auth_code',
               'public_key': 'your_public_key',
               'webhook_secret': 'your_webhook_secret',
               'sandbox': True,  # Use sandbox for testing
           }
       }
   }
   ```

3. **Create Subscription Plans in Paddle**
   - Create products in Paddle Dashboard
   - Copy Plan IDs

4. **Link Plans**
   ```python
   plan = SubscriptionPlan.objects.create(
       name="Professional",
       slug="pro",
       price=29.99,
       billing_period="monthly",
       paddle_plan_id="12345"  # From Paddle Dashboard
   )
   ```

### Webhook Configuration

1. **Add Webhook URL**
   - URL: `https://yourdomain.com/subscriptions/webhooks/paddle/`
   - Events: All subscription events

2. **Verify Webhook Signature**
   - Paddle automatically verifies using public key

### Usage Example

```python
processor = get_payment_processor('paddle')

# Create subscription (Paddle uses checkout)
checkout_url = processor.create_checkout(
    plan_id='12345',
    email='user@example.com',
    passthrough={'user_id': '123'}
)

# Cancel subscription
processor.cancel_subscription(
    subscription_id='sub_12345'
)
```

---

## PayPal Integration

### Setup

1. **Create PayPal Business Account**
   - Sign up at [developer.paypal.com](https://developer.paypal.com)
   - Create REST API app
   - Get Client ID and Secret

2. **Configure Settings**
   ```python
   # settings.py
   WAGTAIL_SUBSCRIPTIONS = {
       'PAYMENT_PROCESSORS': {
           'paypal': {
               'client_id': 'your_client_id',
               'client_secret': 'your_client_secret',
               'mode': 'sandbox',  # or 'live'
               'webhook_id': 'your_webhook_id',
           }
       }
   }
   ```

3. **Create Billing Plans in PayPal**
   ```python
   # Use PayPal API or Dashboard
   # Copy Plan IDs
   ```

4. **Link Plans**
   ```python
   plan = SubscriptionPlan.objects.create(
       name="Professional",
       slug="pro",
       price=29.99,
       billing_period="monthly",
       paypal_plan_id="P-12345"  # From PayPal
   )
   ```

### Webhook Configuration

1. **Add Webhook in PayPal Dashboard**
   - URL: `https://yourdomain.com/subscriptions/webhooks/paypal/`
   - Events:
     - `BILLING.SUBSCRIPTION.CREATED`
     - `BILLING.SUBSCRIPTION.UPDATED`
     - `BILLING.SUBSCRIPTION.CANCELLED`
     - `PAYMENT.SALE.COMPLETED`

### Usage Example

```python
processor = get_payment_processor('paypal')

# Create subscription
subscription = processor.create_subscription(
    plan_id='P-12345',
    subscriber={
        'email_address': 'user@example.com',
        'name': {'given_name': 'John', 'surname': 'Doe'}
    }
)

# Get approval URL
approval_url = subscription['links'][0]['href']
# Redirect user to approval_url

# Cancel subscription
processor.cancel_subscription(
    subscription_id='I-12345',
    reason='Customer request'
)
```

---

## Custom Payment Processor

### Implementation

```python
# myapp/payment_processors.py
from wagtail_subscriptions.payments.base import BasePaymentProcessor
from wagtail_subscriptions.payments.exceptions import PaymentProcessorError

class CustomPaymentProcessor(BasePaymentProcessor):
    """Custom payment processor implementation."""
    
    def __init__(self, config):
        """
        Initialize processor with configuration.
        
        Args:
            config (dict): Processor configuration from settings
        """
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.base_url = config.get('base_url', 'https://api.example.com')
        
    def create_customer(self, email, name=None, metadata=None):
        """
        Create customer in payment processor.
        
        Args:
            email (str): Customer email
            name (str, optional): Customer name
            metadata (dict, optional): Additional data
            
        Returns:
            dict: Customer data with 'id' key
            
        Raises:
            PaymentProcessorError: On API failure
        """
        try:
            response = requests.post(
                f'{self.base_url}/customers',
                json={
                    'email': email,
                    'name': name,
                    'metadata': metadata
                },
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            data = response.json()
            return {
                'id': data['customer_id'],
                'email': data['email']
            }
        except requests.RequestException as e:
            raise PaymentProcessorError(f"Failed to create customer: {str(e)}")
    
    def create_subscription(self, customer_id, plan_id, trial_days=None, **kwargs):
        """
        Create subscription.
        
        Args:
            customer_id (str): Customer ID from create_customer
            plan_id (str): Plan ID in payment processor
            trial_days (int, optional): Trial period
            **kwargs: Additional parameters
            
        Returns:
            dict: Subscription data with 'id' and 'status'
        """
        try:
            payload = {
                'customer_id': customer_id,
                'plan_id': plan_id,
            }
            if trial_days:
                payload['trial_days'] = trial_days
                
            response = requests.post(
                f'{self.base_url}/subscriptions',
                json=payload,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            data = response.json()
            return {
                'id': data['subscription_id'],
                'status': data['status'],
                'current_period_end': data['current_period_end']
            }
        except requests.RequestException as e:
            raise PaymentProcessorError(f"Failed to create subscription: {str(e)}")
    
    def cancel_subscription(self, subscription_id, immediate=False):
        """Cancel subscription."""
        try:
            response = requests.post(
                f'{self.base_url}/subscriptions/{subscription_id}/cancel',
                json={'immediate': immediate},
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise PaymentProcessorError(f"Failed to cancel subscription: {str(e)}")
    
    def update_subscription(self, subscription_id, plan_id=None, **kwargs):
        """Update subscription."""
        try:
            payload = {}
            if plan_id:
                payload['plan_id'] = plan_id
            payload.update(kwargs)
            
            response = requests.patch(
                f'{self.base_url}/subscriptions/{subscription_id}',
                json=payload,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise PaymentProcessorError(f"Failed to update subscription: {str(e)}")
    
    def get_subscription(self, subscription_id):
        """Get subscription details."""
        try:
            response = requests.get(
                f'{self.base_url}/subscriptions/{subscription_id}',
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise PaymentProcessorError(f"Failed to get subscription: {str(e)}")
    
    def verify_webhook(self, payload, signature, secret):
        """
        Verify webhook signature.
        
        Args:
            payload (bytes): Raw webhook payload
            signature (str): Signature from webhook header
            secret (str): Webhook secret
            
        Returns:
            dict: Parsed event data
            
        Raises:
            SignatureVerificationError: On invalid signature
        """
        import hmac
        import hashlib
        from wagtail_subscriptions.payments.exceptions import SignatureVerificationError
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        if not hmac.compare_digest(expected_signature, signature):
            raise SignatureVerificationError("Invalid webhook signature")
        
        # Parse and return event data
        import json
        return json.loads(payload.decode())
```

### Registration

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'myapp'
    
    def ready(self):
        from wagtail_subscriptions.payments import register_processor
        from .payment_processors import CustomPaymentProcessor
        
        register_processor('custom', CustomPaymentProcessor)
```

### Configuration

```python
# settings.py
WAGTAIL_SUBSCRIPTIONS = {
    'PAYMENT_PROCESSORS': {
        'custom': {
            'api_key': 'your_api_key',
            'api_secret': 'your_api_secret',
            'base_url': 'https://api.example.com',
        }
    },
    'DEFAULT_PROCESSOR': 'custom',
}
```

### Webhook View

```python
# myapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from wagtail_subscriptions.payments import get_payment_processor
import json

@csrf_exempt
def custom_webhook(request):
    """Handle webhooks from custom payment processor."""
    processor = get_payment_processor('custom')
    
    # Get signature from header
    signature = request.META.get('HTTP_X_CUSTOM_SIGNATURE')
    
    try:
        # Verify webhook
        event = processor.verify_webhook(
            payload=request.body,
            signature=signature,
            secret=settings.CUSTOM_WEBHOOK_SECRET
        )
        
        # Handle event
        if event['type'] == 'subscription.created':
            # Update local subscription
            pass
        elif event['type'] == 'subscription.updated':
            # Update subscription status
            pass
        elif event['type'] == 'payment.succeeded':
            # Mark invoice as paid
            pass
            
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
```

---

## Testing Payment Integration

### Stripe Test Mode

```python
# Use test API keys
WAGTAIL_SUBSCRIPTIONS = {
    'PAYMENT_PROCESSORS': {
        'stripe': {
            'public_key': 'pk_test_...',
            'secret_key': 'sk_test_...',
            'webhook_secret': 'whsec_...',
        }
    }
}

# Test card numbers
# Success: 4242 4242 4242 4242
# Decline: 4000 0000 0000 0002
```

### Paddle Sandbox

```python
WAGTAIL_SUBSCRIPTIONS = {
    'PAYMENT_PROCESSORS': {
        'paddle': {
            'vendor_id': '12345',
            'auth_code': 'test_auth_code',
            'sandbox': True,  # Enable sandbox mode
        }
    }
}
```

### PayPal Sandbox

```python
WAGTAIL_SUBSCRIPTIONS = {
    'PAYMENT_PROCESSORS': {
        'paypal': {
            'client_id': 'sandbox_client_id',
            'client_secret': 'sandbox_secret',
            'mode': 'sandbox',
        }
    }
}
```

### Unit Tests

```python
# tests/test_payment_processor.py
from django.test import TestCase
from wagtail_subscriptions.payments import get_payment_processor
from unittest.mock import patch, Mock

class CustomProcessorTestCase(TestCase):
    def setUp(self):
        self.processor = get_payment_processor('custom')
    
    @patch('requests.post')
    def test_create_customer(self, mock_post):
        # Mock API response
        mock_post.return_value.json.return_value = {
            'customer_id': 'cus_123',
            'email': 'test@example.com'
        }
        
        # Test customer creation
        customer = self.processor.create_customer(
            email='test@example.com',
            name='Test User'
        )
        
        self.assertEqual(customer['id'], 'cus_123')
        self.assertEqual(customer['email'], 'test@example.com')
```

---

## Best Practices

### Error Handling

```python
from wagtail_subscriptions.payments.exceptions import PaymentProcessorError

try:
    subscription = processor.create_subscription(
        customer_id=customer_id,
        plan_id=plan_id
    )
except PaymentProcessorError as e:
    # Log error
    logger.error(f"Subscription creation failed: {str(e)}")
    # Show user-friendly message
    messages.error(request, "Unable to create subscription. Please try again.")
```

### Idempotency

```python
# Use idempotency keys for Stripe
subscription = processor.create_subscription(
    customer_id=customer_id,
    plan_id=plan_id,
    idempotency_key=f"sub_{user.id}_{plan.id}_{timestamp}"
)
```

### Webhook Security

- Always verify webhook signatures
- Use HTTPS for webhook endpoints
- Implement rate limiting
- Log all webhook events

### Monitoring

- Track webhook processing time
- Monitor failed payment rates
- Alert on webhook failures
- Log all API errors
