# Quick Start Guide

This guide will help you set up your first subscription plan and start accepting payments in under 10 minutes.

## Step 1: Create Your First Module

1. Go to **Wagtail Admin** → **Subscriptions** → **Modules**
2. Click **"Add Module"**
3. Fill in:
   - **Name**: "Core Features"
   - **Slug**: "core-features"
   - **Description**: "Essential features for all users"
4. Click **Save**

## Step 2: Create Features

1. Go to **Subscriptions** → **Features**
2. Click **"Add Feature"** and create:

### Basic Feature
- **Module**: Core Features
- **Name**: "Basic Support"
- **Slug**: "basic-support"
- **Type**: Binary (On/Off)

### Quota Feature
- **Module**: Core Features
- **Name**: "API Calls"
- **Slug**: "api-calls"
- **Type**: Quota (Usage Limit)
- **Default Quota**: 1000
- **Quota Unit**: "calls/month"

## Step 3: Create Subscription Plans

1. Go to **Subscriptions** → **Plans**
2. Create your plans:

### Free Plan
- **Name**: "Free"
- **Slug**: "free"
- **Price**: 0.00
- **Billing Period**: Monthly
- **Trial Period**: 0 days

### Pro Plan
- **Name**: "Professional"
- **Slug**: "professional"
- **Price**: 29.99
- **Billing Period**: Monthly
- **Trial Period**: 14 days

## Step 4: Associate Features with Plans

1. Go to **Subscriptions** → **Plan Features**
2. For each plan, click **"Manage Features"**
3. Add features and set quotas:

### Free Plan Features
- ✅ Basic Support (included)
- ✅ API Calls (quota: 100)

### Pro Plan Features
- ✅ Basic Support (included)
- ✅ API Calls (quota: 10000)

## Step 5: Configure Payment Processor

1. Go to **Subscriptions** → **Settings**
2. Follow the Stripe setup guide:
   - Create Stripe account
   - Get API keys
   - Add webhook endpoint
   - Update Django settings

## Step 6: Add Pricing to Your Site

Add to your template:

```django
{% load subscription_tags %}

<div class="pricing-section">
    {% price_table %}
</div>
```

## Step 7: Test the Flow

1. Visit `/subscriptions/pricing/`
2. Click "Start Free Trial" or "Get Started"
3. Complete the subscription process
4. Check the admin for new customers and subscriptions

## Protecting Content

### In Views
```python
from wagtail_subscriptions.permissions.decorators import feature_required

@feature_required('api-calls')
def api_view(request):
    return JsonResponse({'message': 'API access granted'})
```

### In Templates
```django
{% if request.user.subscriptions.first.has_feature_access:'api-calls' %}
    <a href="/api/">Access API</a>
{% else %}
    <a href="/subscriptions/pricing/">Upgrade to access API</a>
{% endif %}
```

## What's Next?

- [Payment Processor Configuration](payment-processors.md)
- [Advanced Features](advanced-features.md)
- [Customization Guide](customization.md)
- [API Reference](api-reference.md)

## Troubleshooting

### Common Issues

**"No module named 'wagtail_subscriptions'"**
- Make sure you've added it to `INSTALLED_APPS`
- Run `pip install wagtail-subscriptions`

**"Table doesn't exist" errors**
- Run `python manage.py migrate`

**Payment processor not working**
- Check your API keys in settings
- Verify webhook endpoints
- Check the Settings page in admin

Need help? Check our [FAQ](faq.md) or [open an issue](https://github.com/yourusername/wagtail-subscriptions/issues).