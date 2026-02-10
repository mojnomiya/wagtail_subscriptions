# Architecture Overview

## System Design

Wagtail Subscriptions is built with a modular architecture that separates concerns into distinct layers:

```
┌─────────────────────────────────────────────────────────┐
│                    Wagtail Admin UI                      │
│  (Dashboard, Plan Management, Customer Management)       │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   Views & Templates                      │
│  (Pricing Pages, Customer Portal, Subscription Flow)     │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                  Permission Layer                        │
│  (Decorators, Mixins, Middleware, Tenant Manager)        │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   Business Logic                         │
│  (Services, Analytics, Notifications)                    │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    Data Models                           │
│  (Plans, Features, Subscriptions, Invoices)              │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                Payment Processors                        │
│  (Stripe, Paddle, PayPal - Extensible)                   │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Models Layer

**Core Models** (`models/core.py`):
- `SubscriptionPlan`: Defines pricing tiers and billing periods
- `Subscription`: User subscription instances with status tracking
- `Customer`: Extended customer information and billing details

**Feature Models** (`models/features.py`):
- `Module`: Logical grouping of features
- `Feature`: Individual features with quota support
- `PlanFeature`: Many-to-many relationship with quota overrides

**Payment Models** (`models/payments.py`):
- `PaymentMethod`: Stored payment methods
- `Invoice`: Billing records with line items
- `Payment`: Payment transaction history

**Audit Models** (`models/audit.py`):
- `AuditLog`: Complete audit trail for compliance

### 2. Payment Processor Layer

**Base Architecture** (`payments/base.py`):
```python
class BasePaymentProcessor(ABC):
    @abstractmethod
    def create_customer(self, email, name=None, metadata=None):
        """Create customer in payment processor"""
        
    @abstractmethod
    def create_subscription(self, customer_id, plan_id, **kwargs):
        """Create subscription"""
        
    @abstractmethod
    def cancel_subscription(self, subscription_id, immediate=False):
        """Cancel subscription"""
```

**Implementations**:
- `StripePaymentProcessor`: Full Stripe integration
- `PaddlePaymentProcessor`: Paddle Billing API
- `PayPalPaymentProcessor`: PayPal Subscriptions API

**Registry Pattern**:
```python
from wagtail_subscriptions.payments import register_processor, get_payment_processor

# Register custom processor
register_processor('custom', CustomPaymentProcessor)

# Use processor
processor = get_payment_processor('stripe')
```

### 3. Permission System

**Multi-Tenant Support**:
- Auto-detects `django-tenant-schemas`
- Falls back to user-based subscriptions
- Transparent API for both modes

**Permission Decorators**:
```python
@subscription_required
def my_view(request):
    """Requires active subscription"""
    
@feature_required('api_access')
def api_view(request):
    """Requires specific feature"""
```

**View Mixins**:
```python
class MyView(FeatureRequiredMixin, TemplateView):
    required_feature = 'advanced_analytics'
```

**Template Tags**:
```django
{% if request|has_feature:'api_access' %}
    <!-- Feature content -->
{% endif %}
```

### 4. Services Layer

**Invoice Service** (`services/invoice_service.py`):
- Automatic invoice generation
- Tax calculation support
- PDF generation (optional)
- Payment tracking

**Notification Service** (`services/notification_service.py`):
- Trial ending notifications
- Payment failure alerts
- Subscription change confirmations
- Admin notifications

### 5. Admin Interface

**Dashboard** (`views/admin.py`):
- Subscription metrics and KPIs
- Revenue tracking
- Churn analysis
- Recent activity

**Customer Management**:
- Advanced filtering and search
- Bulk operations
- Data export (CSV)
- Audit trail

**Plan Management**:
- Visual plan builder
- Feature assignment
- Pricing configuration
- Trial settings

## Data Flow

### Subscription Creation Flow

```
User selects plan
       ↓
Create Customer in Payment Processor
       ↓
Create Subscription in Payment Processor
       ↓
Webhook confirms subscription
       ↓
Create local Subscription record
       ↓
Grant feature access
       ↓
Send confirmation email
```

### Feature Access Check Flow

```
Request arrives
       ↓
Middleware identifies subscriber (tenant or user)
       ↓
View checks feature requirement
       ↓
Query subscription and plan features
       ↓
Check quota if applicable
       ↓
Grant or deny access
```

### Webhook Processing Flow

```
Webhook received
       ↓
Verify signature
       ↓
Parse event data
       ↓
Update local records
       ↓
Trigger notifications
       ↓
Log audit trail
       ↓
Return 200 OK
```

## Database Schema

### Key Relationships

```
SubscriptionPlan (1) ←→ (N) PlanFeature (N) ←→ (1) Feature
       ↓
       (1)
       ↓
Subscription (N) → (1) User/Tenant
       ↓
       (1)
       ↓
Invoice (N) → (N) Payment
```

### Indexes

Critical indexes for performance:
- `Subscription.user_id` + `status`
- `Subscription.tenant_id` + `status` (multi-tenant)
- `Feature.slug`
- `PlanFeature.plan_id` + `feature_id`
- `AuditLog.timestamp` + `user_id`

## Extension Points

### Custom Payment Processors

```python
from wagtail_subscriptions.payments.base import BasePaymentProcessor

class CustomProcessor(BasePaymentProcessor):
    def create_customer(self, email, name=None, metadata=None):
        # Your implementation
        pass
```

### Custom Notification Handlers

```python
from wagtail_subscriptions.services.notification_service import NotificationService

class CustomNotificationService(NotificationService):
    def send_trial_ending_notification(self, subscription):
        # Your custom logic
        pass
```

### Custom Analytics

```python
from wagtail_subscriptions.analytics import BaseAnalytics

class CustomAnalytics(BaseAnalytics):
    def calculate_mrr(self):
        # Your calculation
        pass
```

## Security Considerations

### Webhook Signature Verification

All payment processor webhooks verify signatures:
```python
# Stripe example
stripe.Webhook.construct_event(
    payload, sig_header, webhook_secret
)
```

### Permission Checks

Multiple layers of permission checking:
1. Django authentication
2. Subscription status validation
3. Feature access verification
4. Quota enforcement

### Audit Logging

All administrative actions are logged:
- User identification
- IP address tracking
- Action details
- Timestamp
- Change metadata

## Performance Optimization

### Query Optimization

- Use `select_related()` for foreign keys
- Use `prefetch_related()` for many-to-many
- Index frequently queried fields
- Cache plan and feature data

### Caching Strategy

```python
from django.core.cache import cache

# Cache plan features
cache_key = f'plan_features_{plan.id}'
features = cache.get(cache_key)
if not features:
    features = plan.get_features()
    cache.set(cache_key, features, 3600)
```

### Background Tasks

Use Celery for:
- Invoice generation
- Email notifications
- Usage tracking
- Analytics calculation

## Testing Strategy

### Unit Tests
- Model methods
- Service functions
- Utility functions

### Integration Tests
- Payment processor interactions
- Webhook handling
- Subscription lifecycle

### End-to-End Tests
- Complete user journey
- Admin workflows
- Multi-tenant scenarios

## Deployment Considerations

### Environment Variables

```bash
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Database Migrations

Always run migrations in production:
```bash
python manage.py migrate wagtail_subscriptions
```

### Static Files

Collect static files for admin interface:
```bash
python manage.py collectstatic
```

### Monitoring

Monitor key metrics:
- Webhook processing time
- Failed payment rate
- Subscription churn
- API response times
