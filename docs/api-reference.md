# API Reference

## Models API

### SubscriptionPlan

**Location**: `wagtail_subscriptions.models.SubscriptionPlan`

#### Fields

- `name` (CharField): Plan display name
- `slug` (SlugField): URL-friendly identifier
- `description` (TextField): Plan description
- `price` (DecimalField): Plan price
- `currency` (CharField): ISO currency code (default: 'USD')
- `billing_period` (CharField): Choices: 'monthly', 'yearly', 'weekly'
- `trial_period_days` (IntegerField): Trial duration (0 = no trial)
- `is_active` (BooleanField): Plan availability
- `stripe_price_id` (CharField): Stripe Price ID
- `paddle_plan_id` (CharField): Paddle Plan ID
- `paypal_plan_id` (CharField): PayPal Plan ID

#### Methods

```python
def get_features(self):
    """
    Get all features included in this plan.
    
    Returns:
        QuerySet: Feature objects with quota annotations
    """

def has_feature(self, feature_slug):
    """
    Check if plan includes a specific feature.
    
    Args:
        feature_slug (str): Feature slug to check
        
    Returns:
        bool: True if feature is included
    """

def get_feature_quota(self, feature_slug):
    """
    Get quota for a specific feature.
    
    Args:
        feature_slug (str): Feature slug
        
    Returns:
        int or None: Quota value, None if unlimited
    """
```

#### Example Usage

```python
from wagtail_subscriptions.models import SubscriptionPlan

# Create a plan
plan = SubscriptionPlan.objects.create(
    name="Professional",
    slug="pro",
    price=29.99,
    billing_period="monthly",
    trial_period_days=14
)

# Check features
if plan.has_feature('api_access'):
    quota = plan.get_feature_quota('api_access')
    print(f"API calls allowed: {quota}")
```

---

### Subscription

**Location**: `wagtail_subscriptions.models.Subscription`

#### Fields

- `user` (ForeignKey): User who owns subscription
- `tenant` (ForeignKey): Tenant (multi-tenant mode)
- `plan` (ForeignKey): Associated subscription plan
- `status` (CharField): Choices: 'active', 'trialing', 'past_due', 'canceled', 'unpaid'
- `current_period_start` (DateTimeField): Billing period start
- `current_period_end` (DateTimeField): Billing period end
- `trial_start` (DateTimeField): Trial start date
- `trial_end` (DateTimeField): Trial end date
- `canceled_at` (DateTimeField): Cancellation timestamp
- `stripe_subscription_id` (CharField): Stripe Subscription ID
- `paddle_subscription_id` (CharField): Paddle Subscription ID
- `paypal_subscription_id` (CharField): PayPal Subscription ID

#### Properties

```python
@property
def is_active(self):
    """Check if subscription is active or trialing."""
    return self.status in ['active', 'trialing']

@property
def is_trial(self):
    """Check if subscription is in trial period."""
    return self.status == 'trialing'

@property
def days_until_renewal(self):
    """Calculate days until next billing."""
    if self.current_period_end:
        delta = self.current_period_end - timezone.now()
        return delta.days
    return None
```

#### Methods

```python
def has_feature_access(self, feature_slug):
    """
    Check if subscription has access to a feature.
    
    Args:
        feature_slug (str): Feature slug to check
        
    Returns:
        bool: True if feature is accessible
    """

def get_feature_quota(self, feature_slug):
    """
    Get remaining quota for a feature.
    
    Args:
        feature_slug (str): Feature slug
        
    Returns:
        int or None: Remaining quota, None if unlimited
    """

def cancel(self, immediate=False):
    """
    Cancel the subscription.
    
    Args:
        immediate (bool): Cancel immediately vs end of period
        
    Returns:
        bool: Success status
    """

def reactivate(self):
    """
    Reactivate a canceled subscription.
    
    Returns:
        bool: Success status
    """
```

#### Example Usage

```python
from wagtail_subscriptions.models import Subscription

# Get user's subscription
subscription = request.user.subscriptions.filter(status='active').first()

# Check feature access
if subscription.has_feature_access('advanced_analytics'):
    # Show analytics dashboard
    pass

# Check quota
api_quota = subscription.get_feature_quota('api_calls')
if api_quota and api_quota > 0:
    # Make API call
    pass

# Cancel subscription
subscription.cancel(immediate=False)  # Cancel at period end
```

---

### Feature

**Location**: `wagtail_subscriptions.models.Feature`

#### Fields

- `name` (CharField): Feature display name
- `slug` (SlugField): URL-friendly identifier
- `description` (TextField): Feature description
- `module` (ForeignKey): Parent module
- `feature_type` (CharField): Choices: 'boolean', 'quota'
- `default_quota` (IntegerField): Default quota (null = unlimited)

#### Methods

```python
def is_available_for_plan(self, plan):
    """
    Check if feature is available in a plan.
    
    Args:
        plan (SubscriptionPlan): Plan to check
        
    Returns:
        bool: True if available
    """
```

---

## Payment Processors API

### BasePaymentProcessor

**Location**: `wagtail_subscriptions.payments.base.BasePaymentProcessor`

#### Abstract Methods

```python
@abstractmethod
def create_customer(self, email, name=None, metadata=None):
    """
    Create a customer in the payment processor.
    
    Args:
        email (str): Customer email
        name (str, optional): Customer name
        metadata (dict, optional): Additional metadata
        
    Returns:
        dict: Customer data with 'id' key
        
    Raises:
        PaymentProcessorError: On failure
    """

@abstractmethod
def create_subscription(self, customer_id, plan_id, trial_days=None, **kwargs):
    """
    Create a subscription.
    
    Args:
        customer_id (str): Payment processor customer ID
        plan_id (str): Payment processor plan ID
        trial_days (int, optional): Trial period in days
        **kwargs: Additional processor-specific parameters
        
    Returns:
        dict: Subscription data with 'id' and 'status' keys
        
    Raises:
        PaymentProcessorError: On failure
    """

@abstractmethod
def cancel_subscription(self, subscription_id, immediate=False):
    """
    Cancel a subscription.
    
    Args:
        subscription_id (str): Payment processor subscription ID
        immediate (bool): Cancel immediately vs end of period
        
    Returns:
        dict: Updated subscription data
        
    Raises:
        PaymentProcessorError: On failure
    """

@abstractmethod
def update_subscription(self, subscription_id, plan_id=None, **kwargs):
    """
    Update a subscription.
    
    Args:
        subscription_id (str): Payment processor subscription ID
        plan_id (str, optional): New plan ID
        **kwargs: Additional parameters
        
    Returns:
        dict: Updated subscription data
    """

@abstractmethod
def get_subscription(self, subscription_id):
    """
    Retrieve subscription details.
    
    Args:
        subscription_id (str): Payment processor subscription ID
        
    Returns:
        dict: Subscription data
    """

@abstractmethod
def verify_webhook(self, payload, signature, secret):
    """
    Verify webhook signature.
    
    Args:
        payload (bytes): Raw webhook payload
        signature (str): Webhook signature
        secret (str): Webhook secret
        
    Returns:
        dict: Parsed event data
        
    Raises:
        SignatureVerificationError: On invalid signature
    """
```

#### Example: Custom Processor

```python
from wagtail_subscriptions.payments.base import BasePaymentProcessor
from wagtail_subscriptions.payments import register_processor

class CustomPaymentProcessor(BasePaymentProcessor):
    def __init__(self, config):
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        
    def create_customer(self, email, name=None, metadata=None):
        # Your implementation
        response = your_api.customers.create(
            email=email,
            name=name,
            metadata=metadata
        )
        return {'id': response.id, 'email': response.email}
        
    def create_subscription(self, customer_id, plan_id, trial_days=None, **kwargs):
        # Your implementation
        response = your_api.subscriptions.create(
            customer=customer_id,
            plan=plan_id,
            trial_period_days=trial_days
        )
        return {
            'id': response.id,
            'status': response.status,
            'current_period_end': response.current_period_end
        }
        
    # Implement other abstract methods...

# Register your processor
register_processor('custom', CustomPaymentProcessor)
```

---

### StripePaymentProcessor

**Location**: `wagtail_subscriptions.payments.stripe.StripePaymentProcessor`

#### Configuration

```python
WAGTAIL_SUBSCRIPTIONS = {
    'PAYMENT_PROCESSORS': {
        'stripe': {
            'public_key': 'pk_test_...',
            'secret_key': 'sk_test_...',
            'webhook_secret': 'whsec_...',
        }
    }
}
```

#### Additional Methods

```python
def create_payment_intent(self, amount, currency='usd', customer_id=None):
    """
    Create a Stripe Payment Intent.
    
    Args:
        amount (int): Amount in cents
        currency (str): Currency code
        customer_id (str, optional): Stripe customer ID
        
    Returns:
        dict: Payment Intent data
    """

def attach_payment_method(self, payment_method_id, customer_id):
    """
    Attach payment method to customer.
    
    Args:
        payment_method_id (str): Stripe PaymentMethod ID
        customer_id (str): Stripe Customer ID
        
    Returns:
        dict: PaymentMethod data
    """
```

---

## Permission System API

### Decorators

**Location**: `wagtail_subscriptions.permissions.decorators`

#### subscription_required

```python
from wagtail_subscriptions.permissions.decorators import subscription_required

@subscription_required
def my_view(request):
    """
    Requires user to have an active subscription.
    Redirects to pricing page if no subscription.
    """
    return render(request, 'my_template.html')

@subscription_required(redirect_url='/custom-pricing/')
def custom_redirect_view(request):
    """Custom redirect URL for non-subscribers."""
    pass
```

#### feature_required

```python
from wagtail_subscriptions.permissions.decorators import feature_required

@feature_required('api_access')
def api_view(request):
    """
    Requires specific feature access.
    Returns 403 if feature not available.
    """
    return JsonResponse({'data': 'api response'})

@feature_required('api_access', redirect_url='/upgrade/')
def api_with_redirect(request):
    """Redirect instead of 403."""
    pass
```

### View Mixins

**Location**: `wagtail_subscriptions.permissions.mixins`

#### SubscriptionRequiredMixin

```python
from django.views.generic import TemplateView
from wagtail_subscriptions.permissions.mixins import SubscriptionRequiredMixin

class MyView(SubscriptionRequiredMixin, TemplateView):
    template_name = 'my_template.html'
    subscription_redirect_url = '/pricing/'  # Optional
```

#### FeatureRequiredMixin

```python
from django.views.generic import TemplateView
from wagtail_subscriptions.permissions.mixins import FeatureRequiredMixin

class AnalyticsView(FeatureRequiredMixin, TemplateView):
    template_name = 'analytics.html'
    required_feature = 'advanced_analytics'
    feature_redirect_url = '/upgrade/'  # Optional
```

### Template Tags

**Location**: `wagtail_subscriptions.templatetags.subscription_tags`

#### has_feature

```django
{% load subscription_tags %}

{% if request|has_feature:'api_access' %}
    <a href="/api/docs/">API Documentation</a>
{% endif %}

{% if request|has_feature:'advanced_analytics' %}
    <div class="analytics-dashboard">
        <!-- Analytics content -->
    </div>
{% endif %}
```

#### subscription_info

```django
{% load subscription_tags %}

{% subscription_info as sub_info %}

{% if sub_info %}
    <div class="subscription-badge">
        <span>{{ sub_info.plan }}</span>
        {% if sub_info.is_trial %}
            <span class="trial-badge">Trial</span>
        {% endif %}
    </div>
    
    <p>Subscriber: {{ sub_info.name }} ({{ sub_info.type }})</p>
    <p>Status: {{ sub_info.status }}</p>
{% endif %}
```

#### price_table

```django
{% load subscription_tags %}

<!-- Basic usage -->
{% price_table %}

<!-- With options -->
{% price_table show_trial=True highlight_plan="pro" %}
```

---

## Services API

### InvoiceService

**Location**: `wagtail_subscriptions.services.invoice_service.InvoiceService`

#### Methods

```python
@staticmethod
def create_invoice_for_subscription(subscription, tax_rate=None):
    """
    Create invoice for a subscription.
    
    Args:
        subscription (Subscription): Subscription instance
        tax_rate (Decimal, optional): Tax rate (e.g., 0.08 for 8%)
        
    Returns:
        Invoice: Created invoice instance
    """

@staticmethod
def mark_invoice_paid(invoice, payment_amount, payment_method=None):
    """
    Mark invoice as paid.
    
    Args:
        invoice (Invoice): Invoice instance
        payment_amount (Decimal): Amount paid
        payment_method (str, optional): Payment method used
        
    Returns:
        Payment: Created payment record
    """

@staticmethod
def generate_pdf(invoice):
    """
    Generate PDF for invoice.
    
    Args:
        invoice (Invoice): Invoice instance
        
    Returns:
        bytes: PDF file content
    """
```

#### Example Usage

```python
from wagtail_subscriptions.services.invoice_service import InvoiceService
from decimal import Decimal

# Create invoice
invoice = InvoiceService.create_invoice_for_subscription(
    subscription=subscription,
    tax_rate=Decimal('0.08')  # 8% tax
)

# Mark as paid
payment = InvoiceService.mark_invoice_paid(
    invoice=invoice,
    payment_amount=invoice.total,
    payment_method='stripe'
)

# Generate PDF
pdf_content = InvoiceService.generate_pdf(invoice)
```

### NotificationService

**Location**: `wagtail_subscriptions.services.notification_service.NotificationService`

#### Methods

```python
@staticmethod
def send_trial_ending_notification(subscription, days_remaining=3):
    """
    Send trial ending notification.
    
    Args:
        subscription (Subscription): Subscription instance
        days_remaining (int): Days until trial ends
    """

@staticmethod
def send_payment_failed_notification(subscription, invoice=None):
    """
    Send payment failure notification.
    
    Args:
        subscription (Subscription): Subscription instance
        invoice (Invoice, optional): Failed invoice
    """

@staticmethod
def send_subscription_canceled_notification(subscription):
    """
    Send cancellation confirmation.
    
    Args:
        subscription (Subscription): Canceled subscription
    """
```

---

## Utility Functions

### Registry Functions

**Location**: `wagtail_subscriptions.payments`

```python
from wagtail_subscriptions.payments import (
    register_processor,
    get_payment_processor,
    get_available_processors
)

# Register processor
register_processor('custom', CustomPaymentProcessor)

# Get processor instance
processor = get_payment_processor('stripe')

# List available processors
processors = get_available_processors()  # ['stripe', 'paddle', 'paypal', 'custom']
```

### Analytics Functions

**Location**: `wagtail_subscriptions.analytics`

```python
from wagtail_subscriptions.analytics import (
    calculate_mrr,
    calculate_churn_rate,
    get_subscription_metrics
)

# Calculate Monthly Recurring Revenue
mrr = calculate_mrr()

# Calculate churn rate
churn = calculate_churn_rate(period='monthly')

# Get comprehensive metrics
metrics = get_subscription_metrics()
# Returns: {
#     'total_subscriptions': 150,
#     'active_subscriptions': 120,
#     'mrr': 3599.70,
#     'churn_rate': 0.05,
#     'growth_rate': 0.15
# }
```

---

## Signals

**Location**: `wagtail_subscriptions.signals`

### Available Signals

```python
from wagtail_subscriptions.signals import (
    subscription_created,
    subscription_updated,
    subscription_canceled,
    payment_succeeded,
    payment_failed
)

# Connect to signals
@receiver(subscription_created)
def on_subscription_created(sender, subscription, **kwargs):
    """Handle new subscription."""
    print(f"New subscription: {subscription.id}")

@receiver(payment_failed)
def on_payment_failed(sender, subscription, invoice, **kwargs):
    """Handle payment failure."""
    # Send alert, update status, etc.
    pass
```

---

## Management Commands

### setup_subscription_permissions

```bash
python manage.py setup_subscription_permissions
```

Sets up Django permissions for subscription management.

### subscription_maintenance

```bash
# Run all maintenance tasks
python manage.py subscription_maintenance --all

# Check trial expirations
python manage.py subscription_maintenance --check-trials

# Check failed payments
python manage.py subscription_maintenance --check-payments

# Cleanup expired subscriptions
python manage.py subscription_maintenance --cleanup-expired
```

### sync_tenant_plans

```bash
# Sync plans for all tenants (multi-tenant mode)
python manage.py sync_tenant_plans
```
