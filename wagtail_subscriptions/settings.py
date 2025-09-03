from django.conf import settings

# Default settings for wagtail-subscriptions
WAGTAIL_SUBSCRIPTIONS_DEFAULTS = {
    'DEFAULT_CURRENCY': 'USD',
    'TRIAL_PERIOD_DAYS': 14,
    'DEFAULT_PROCESSOR': 'stripe',
    'PAYMENT_PROCESSORS': {
        'stripe': {
            'public_key': '',
            'secret_key': '',
            'webhook_secret': '',
        }
    },
    'FEATURES': {
        'USAGE_TRACKING': True,
        'CUSTOMER_PORTAL': True,
        'INVOICE_GENERATION': True,
    },
    'PERMISSIONS': {
        'AUTO_CREATE_GROUPS': True,
        'SYNC_PERMISSIONS': True,
    }
}

# Get user settings and merge with defaults
user_settings = getattr(settings, 'WAGTAIL_SUBSCRIPTIONS', {})
WAGTAIL_SUBSCRIPTIONS = {**WAGTAIL_SUBSCRIPTIONS_DEFAULTS, **user_settings}