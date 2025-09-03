Installation
============

Requirements
------------

* Python 3.8+
* Django 3.2+
* Wagtail 4.0+

Install from PyPI
-----------------

Basic installation::

    pip install wagtail-subscriptions

With Stripe support::

    pip install wagtail-subscriptions[stripe]

With all payment processors::

    pip install wagtail-subscriptions[stripe,paddle,paypal]

Development installation::

    pip install wagtail-subscriptions[dev]

Configuration
-------------

Add to your Django settings::

    INSTALLED_APPS = [
        # ... your existing apps
        'wagtail_subscriptions',
    ]

    WAGTAIL_SUBSCRIPTIONS = {
        'DEFAULT_CURRENCY': 'USD',
        'TRIAL_PERIOD_DAYS': 14,
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
        }
    }

URL Configuration
-----------------

Add to your main urls.py::

    from django.urls import path, include

    urlpatterns = [
        # ... your existing URLs
        path('subscriptions/', include('wagtail_subscriptions.urls')),
    ]

Database Migration
------------------

Run migrations to create the necessary database tables::

    python manage.py migrate