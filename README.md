# Wagtail Subscriptions

A comprehensive subscription management system for Wagtail CMS that provides everything you need to build a SaaS application with subscription billing.

## Features

🚀 **Complete Subscription Management**
- Multiple subscription plans with flexible billing periods
- Feature-based access control
- Trial periods and plan upgrades
- Customer portal and billing management

💳 **Payment Integration**
- Stripe integration (built-in)
- Paddle support
- PayPal integration
- Extensible payment processor architecture

🎛️ **Admin Dashboard**
- Beautiful Wagtail-integrated admin interface
- Plan and feature management
- Customer overview and analytics
- Payment processor configuration

🎨 **Frontend Components**
- Responsive pricing tables
- Modern UI with Tailwind CSS
- Customizable templates
- Template tags for easy integration

## Quick Start

### Installation

```bash
pip install wagtail-subscriptions
```

### Settings

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... your apps
    'wagtail_subscriptions',
]
```

Configure payment processors:

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

### URLs

```python
from django.urls import path, include

urlpatterns = [
    # ... your URLs
    path('subscriptions/', include('wagtail_subscriptions.urls')),
]
```

### Migrate

```bash
python manage.py migrate
python manage.py setup_subscription_permissions
```

## Usage

### Create Subscription Plans

1. Go to Wagtail Admin → Subscriptions → Plans
2. Create your subscription plans with pricing
3. Add modules and features
4. Associate features with plans

### Display Pricing

Use the built-in template tag:

```django
{% load subscription_tags %}
{% price_table %}
```

### Protect Views

```python
from wagtail_subscriptions.permissions.decorators import subscription_required, feature_required

@subscription_required
def my_view(request):
    return render(request, 'my_template.html')

@feature_required('advanced_analytics')
def analytics_view(request):
    return render(request, 'analytics.html')
```

### Check Permissions in Templates

```django
{% if request.user.subscriptions.first.has_feature_access:'api_access' %}
    <a href="/api/">API Documentation</a>
{% endif %}
```

## Documentation

### Models

- **SubscriptionPlan**: Define pricing and billing periods
- **Module**: Organize features into logical groups
- **Feature**: Individual features with quota support
- **PlanFeature**: Associate features with plans
- **Subscription**: User subscriptions and billing
- **Customer**: Extended customer information

### Payment Processors

#### Stripe Setup

1. Create Stripe account
2. Get API keys from dashboard
3. Add webhook endpoint: `/subscriptions/webhooks/stripe/`
4. Configure in Django settings

#### Paddle Setup

1. Create Paddle account
2. Get Vendor ID and Auth Code
3. Configure webhook URL
4. Add to Django settings

### Template Tags

```django
{% load subscription_tags %}

<!-- Basic pricing table -->
{% price_table %}

<!-- Custom options -->
{% price_table show_trial=False highlight_plan="pro" %}

<!-- Check feature access -->
{% if subscription|has_feature:"advanced_reports" %}
    <!-- Feature content -->
{% endif %}
```

### Management Commands

```bash
# Set up permissions
python manage.py setup_subscription_permissions

# Create sample data
python manage.py create_sample_plans
```

## API Reference

### Subscription Model Methods

```python
subscription = request.user.subscriptions.first()

# Check feature access
subscription.has_feature_access('feature_slug')

# Get feature quota
subscription.get_feature_quota('feature_slug')

# Check if active
subscription.is_active

# Check if in trial
subscription.is_trial
```

### Permission Mixins

```python
from wagtail_subscriptions.permissions.mixins import (
    SubscriptionRequiredMixin, 
    FeatureRequiredMixin
)

class MyView(FeatureRequiredMixin, TemplateView):
    required_feature = 'advanced_analytics'
    template_name = 'my_template.html'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://wagtail-subscriptions.readthedocs.io/
- Issues: https://github.com/yourusername/wagtail-subscriptions/issues
- Discussions: https://github.com/yourusername/wagtail-subscriptions/discussions