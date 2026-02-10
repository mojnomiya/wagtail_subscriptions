# Multi-Tenant Setup Guide

## Overview

Wagtail Subscriptions automatically detects and supports multi-tenant architectures using `django-tenant-schemas` or similar packages. In multi-tenant mode, subscriptions are associated with tenants rather than individual users.

## Architecture

### Single-Tenant Mode (Default)
```
User → Subscription → Plan → Features
```

### Multi-Tenant Mode
```
Tenant → Subscription → Plan → Features
  ↓
Users (inherit tenant's subscription)
```

## Setup with django-tenant-schemas

### 1. Install Dependencies

```bash
pip install django-tenant-schemas
pip install wagtail-subscriptions
```

### 2. Configure Django Settings

```python
# settings.py

INSTALLED_APPS = [
    'tenant_schemas',  # Must be first
    'django.contrib.contenttypes',
    'django.contrib.auth',
    # ... other apps
    'wagtail_subscriptions',
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'tenant_schemas.postgresql_backend',
        'NAME': 'your_database',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Tenant configuration
TENANT_MODEL = "customers.Client"  # Your tenant model
TENANT_DOMAIN_MODEL = "customers.Domain"

# Shared apps (available to all tenants)
SHARED_APPS = [
    'tenant_schemas',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'wagtail_subscriptions',  # Shared for plan management
]

# Tenant-specific apps
TENANT_APPS = [
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    # Your tenant-specific apps
]

# Middleware
MIDDLEWARE = [
    'tenant_schemas.middleware.TenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware
]

# Public schema name
PUBLIC_SCHEMA_NAME = 'public'
```

### 3. Create Tenant Model

```python
# customers/models.py
from django.db import models
from tenant_schemas.models import TenantMixin

class Client(TenantMixin):
    """Tenant model with subscription support."""
    
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    
    # Subscription will be automatically linked
    # via wagtail_subscriptions.models.Subscription.tenant
    
    auto_create_schema = True
    auto_drop_schema = True
    
    def __str__(self):
        return self.name

class Domain(models.Model):
    """Domain model for tenant routing."""
    
    domain = models.CharField(max_length=253, unique=True, db_index=True)
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='domains')
    is_primary = models.BooleanField(default=True)
    
    def __str__(self):
        return self.domain
```

### 4. Run Migrations

```bash
# Create public schema and shared tables
python manage.py migrate_schemas --shared

# Create tenant schemas
python manage.py migrate_schemas
```

### 5. Create Subscription Plans (Public Schema)

```python
# In Django shell or management command
from django.core.management import call_command
from tenant_schemas.utils import schema_context

# Switch to public schema
with schema_context('public'):
    from wagtail_subscriptions.models import SubscriptionPlan, Feature, Module
    
    # Create plans
    starter = SubscriptionPlan.objects.create(
        name="Starter",
        slug="starter",
        price=9.99,
        billing_period="monthly"
    )
    
    pro = SubscriptionPlan.objects.create(
        name="Professional",
        slug="pro",
        price=29.99,
        billing_period="monthly"
    )
    
    # Create features
    module = Module.objects.create(name="Core Features")
    
    users_feature = Feature.objects.create(
        name="User Accounts",
        slug="user_accounts",
        module=module,
        feature_type="quota",
        default_quota=10
    )
    
    # Assign features to plans
    starter.plan_features.create(feature=users_feature, quota=5)
    pro.plan_features.create(feature=users_feature, quota=50)
```

## Usage in Multi-Tenant Mode

### Creating Tenant with Subscription

```python
from customers.models import Client, Domain
from wagtail_subscriptions.models import Subscription, SubscriptionPlan
from wagtail_subscriptions.payments import get_payment_processor

# Create tenant
tenant = Client.objects.create(
    schema_name='acme_corp',
    name='Acme Corporation'
)

# Create domain
Domain.objects.create(
    domain='acme.example.com',
    tenant=tenant,
    is_primary=True
)

# Get plan
plan = SubscriptionPlan.objects.get(slug='pro')

# Create subscription for tenant
processor = get_payment_processor('stripe')

# Create customer in payment processor
customer = processor.create_customer(
    email='billing@acme.com',
    name='Acme Corporation',
    metadata={'tenant_id': tenant.id}
)

# Create subscription
subscription = Subscription.objects.create(
    tenant=tenant,  # Link to tenant, not user
    plan=plan,
    status='active',
    stripe_customer_id=customer['id']
)
```

### Checking Feature Access

```python
# In views (automatic tenant detection)
from wagtail_subscriptions.permissions.decorators import feature_required

@feature_required('advanced_analytics')
def analytics_view(request):
    """
    Automatically checks current tenant's subscription.
    TenantMiddleware sets request.tenant.
    """
    return render(request, 'analytics.html')
```

### Template Usage

```django
{% load subscription_tags %}

<!-- Automatically uses current tenant's subscription -->
{% if request|has_feature:'api_access' %}
    <a href="/api/">API Access</a>
{% endif %}

<!-- Get tenant subscription info -->
{% subscription_info as sub_info %}
<div class="tenant-subscription">
    <h3>{{ sub_info.name }}</h3>
    <p>Plan: {{ sub_info.plan }}</p>
    <p>Type: {{ sub_info.type }}</p>  <!-- Will show "tenant" -->
</div>
```

### Programmatic Access

```python
from wagtail_subscriptions.permissions.tenant_manager import TenantSubscriptionManager

# Get tenant's subscription
manager = TenantSubscriptionManager()
subscription = manager.get_subscription(request)

# Check feature access
if subscription and subscription.has_feature_access('api_access'):
    # Grant access
    pass

# Get feature quota
quota = subscription.get_feature_quota('api_calls')
```

## Tenant Provisioning Workflow

### Complete Tenant Setup

```python
# management/commands/create_tenant.py
from django.core.management.base import BaseCommand
from customers.models import Client, Domain
from wagtail_subscriptions.models import Subscription, SubscriptionPlan
from wagtail_subscriptions.payments import get_payment_processor

class Command(BaseCommand):
    help = 'Create new tenant with subscription'
    
    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str)
        parser.add_argument('domain', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('plan_slug', type=str)
    
    def handle(self, *args, **options):
        # Create tenant
        tenant = Client.objects.create(
            schema_name=options['schema_name'],
            name=options['name']
        )
        self.stdout.write(f"Created tenant: {tenant.name}")
        
        # Create domain
        domain = Domain.objects.create(
            domain=options['domain'],
            tenant=tenant,
            is_primary=True
        )
        self.stdout.write(f"Created domain: {domain.domain}")
        
        # Get plan
        plan = SubscriptionPlan.objects.get(slug=options['plan_slug'])
        
        # Create payment processor customer
        processor = get_payment_processor('stripe')
        customer = processor.create_customer(
            email=options['email'],
            name=options['name'],
            metadata={'tenant_id': tenant.id}
        )
        
        # Create subscription
        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status='trialing' if plan.trial_period_days > 0 else 'active',
            stripe_customer_id=customer['id']
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created tenant with {plan.name} subscription"
            )
        )
```

Usage:
```bash
python manage.py create_tenant \
    acme_corp \
    acme.example.com \
    "Acme Corporation" \
    billing@acme.com \
    pro
```

## Tenant-Aware Admin

### Custom Admin Views

```python
# admin/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from wagtail_subscriptions.models import Subscription

@staff_member_required
def tenant_subscriptions(request):
    """View all tenant subscriptions."""
    subscriptions = Subscription.objects.filter(
        tenant__isnull=False
    ).select_related('tenant', 'plan')
    
    return render(request, 'admin/tenant_subscriptions.html', {
        'subscriptions': subscriptions
    })
```

### Wagtail Admin Integration

```python
# wagtail_hooks.py
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse

@hooks.register('register_admin_menu_item')
def register_tenant_menu():
    return MenuItem(
        'Tenant Subscriptions',
        reverse('admin:tenant_subscriptions'),
        icon_name='group',
        order=400
    )
```

## Subscription Management

### Upgrade/Downgrade Tenant Plan

```python
from wagtail_subscriptions.models import Subscription
from wagtail_subscriptions.payments import get_payment_processor

def change_tenant_plan(tenant, new_plan):
    """Change tenant's subscription plan."""
    subscription = Subscription.objects.get(tenant=tenant, status='active')
    processor = get_payment_processor('stripe')
    
    # Update in payment processor
    processor.update_subscription(
        subscription_id=subscription.stripe_subscription_id,
        plan_id=new_plan.stripe_price_id,
        prorate=True
    )
    
    # Update local record
    subscription.plan = new_plan
    subscription.save()
    
    return subscription
```

### Cancel Tenant Subscription

```python
def cancel_tenant_subscription(tenant, immediate=False):
    """Cancel tenant's subscription."""
    subscription = Subscription.objects.get(tenant=tenant, status='active')
    
    # Cancel in payment processor
    subscription.cancel(immediate=immediate)
    
    if immediate:
        # Optionally disable tenant
        tenant.is_active = False
        tenant.save()
```

## Billing Portal

### Tenant Billing View

```python
# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from wagtail_subscriptions.models import Subscription, Invoice

@login_required
def tenant_billing(request):
    """Tenant billing portal."""
    tenant = request.tenant
    subscription = Subscription.objects.filter(
        tenant=tenant,
        status__in=['active', 'trialing']
    ).first()
    
    invoices = Invoice.objects.filter(
        subscription=subscription
    ).order_by('-created_at')
    
    return render(request, 'billing/portal.html', {
        'subscription': subscription,
        'invoices': invoices,
        'tenant': tenant
    })
```

## Webhooks in Multi-Tenant

### Handling Tenant Webhooks

```python
# views/webhooks.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from wagtail_subscriptions.payments import get_payment_processor
from wagtail_subscriptions.models import Subscription

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks for tenant subscriptions."""
    processor = get_payment_processor('stripe')
    
    try:
        event = processor.verify_webhook(
            payload=request.body,
            signature=request.META.get('HTTP_STRIPE_SIGNATURE'),
            secret=settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'customer.subscription.updated':
            # Find subscription by stripe_subscription_id
            subscription = Subscription.objects.get(
                stripe_subscription_id=event['data']['object']['id']
            )
            
            # Update subscription status
            subscription.status = event['data']['object']['status']
            subscription.save()
            
            # If subscription is canceled, optionally disable tenant
            if subscription.status == 'canceled':
                tenant = subscription.tenant
                tenant.is_active = False
                tenant.save()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
```

## Testing Multi-Tenant Setup

### Test Case Example

```python
# tests/test_multi_tenant.py
from django.test import TestCase
from tenant_schemas.test.cases import TenantTestCase
from customers.models import Client
from wagtail_subscriptions.models import Subscription, SubscriptionPlan

class MultiTenantSubscriptionTest(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.plan = SubscriptionPlan.objects.create(
            name="Test Plan",
            slug="test",
            price=9.99
        )
    
    def test_tenant_subscription(self):
        """Test tenant subscription creation."""
        subscription = Subscription.objects.create(
            tenant=self.tenant,
            plan=self.plan,
            status='active'
        )
        
        self.assertEqual(subscription.tenant, self.tenant)
        self.assertTrue(subscription.is_active)
    
    def test_feature_access(self):
        """Test tenant feature access."""
        subscription = Subscription.objects.create(
            tenant=self.tenant,
            plan=self.plan,
            status='active'
        )
        
        # Test feature access
        has_access = subscription.has_feature_access('test_feature')
        self.assertTrue(has_access)
```

## Best Practices

### 1. Tenant Isolation
- Always use `schema_context` when accessing tenant data
- Never mix public and tenant schemas in queries
- Use middleware for automatic tenant detection

### 2. Subscription Management
- Link subscriptions to tenants, not users
- Handle subscription cancellation gracefully
- Implement grace periods for payment failures

### 3. Feature Access
- Cache feature checks per request
- Use middleware for automatic tenant detection
- Implement quota tracking per tenant

### 4. Billing
- Store billing contact separately from tenant admin
- Send invoices to billing contact
- Implement payment retry logic

### 5. Monitoring
- Track subscription status per tenant
- Monitor feature usage per tenant
- Alert on payment failures
- Log all subscription changes

## Troubleshooting

### Common Issues

**Issue**: Features not accessible after subscription creation
```python
# Solution: Clear cache
from django.core.cache import cache
cache.clear()
```

**Issue**: Tenant not detected in views
```python
# Solution: Ensure TenantMiddleware is properly configured
MIDDLEWARE = [
    'tenant_schemas.middleware.TenantMiddleware',  # Must be first
    # ... other middleware
]
```

**Issue**: Subscription queries returning wrong tenant
```python
# Solution: Always filter by tenant
subscription = Subscription.objects.filter(
    tenant=request.tenant,
    status='active'
).first()
```
