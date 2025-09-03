# Installation Guide

## Requirements

- Python 3.8+
- Django 3.2+
- Wagtail 4.0+

## Installation

### 1. Install Package

```bash
pip install wagtail-subscriptions
```

### 2. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... your existing apps
    'wagtail_subscriptions',
    # ... other apps
]
```

### 3. Configure Settings

```python
# settings.py
WAGTAIL_SUBSCRIPTIONS = {
    'PAYMENT_PROCESSORS': {
        'stripe': {
            'public_key': 'pk_test_...',
            'secret_key': 'sk_test_...',
            'webhook_secret': 'whsec_...',
        },
        'paddle': {
            'vendor_id': '12345',
            'vendor_auth_code': 'your_auth_code',
            'public_key': 'your_public_key',
        },
        'paypal': {
            'client_id': 'your_client_id',
            'client_secret': 'your_client_secret',
            'mode': 'sandbox',  # or 'live'
        }
    },
    'CURRENCY': 'USD',
    'TRIAL_PERIOD_DAYS': 14,
}
```

### 4. Add URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... your existing URLs
    path('subscriptions/', include('wagtail_subscriptions.urls')),
    # ... other URLs
]
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Set Up Permissions

```bash
python manage.py setup_subscription_permissions
```

### 7. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

## Verification

1. Start your development server:
```bash
python manage.py runserver
```

2. Visit the admin at `/admin/`
3. Look for "Subscriptions" in the left menu
4. Create your first subscription plan

## Next Steps

- [Configuration Guide](configuration.md)
- [Creating Your First Plan](quickstart.md)
- [Payment Processor Setup](payment-processors.md)