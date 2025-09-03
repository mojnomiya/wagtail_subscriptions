Wagtail Subscriptions Documentation
===================================

A comprehensive subscription management package for Wagtail CMS that enables SaaS businesses to manage subscription plans, features, permissions, and payment integrations seamlessly within their Wagtail admin interface.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   models
   payments
   permissions
   analytics
   api

Features
--------

* **Subscription Plan Management**: Visual plan builder with flexible pricing models
* **Feature System**: Hierarchical feature organization with usage quotas
* **Payment Integration**: Multi-provider support (Stripe, Paddle, PayPal)
* **Permission Control**: Django permission integration with subscription-based access
* **Wagtail Integration**: Native admin interface and content integration
* **Customer Portal**: Self-service subscription management
* **Analytics**: Built-in reporting and usage tracking

Quick Start
-----------

1. Install the package::

    pip install wagtail-subscriptions[stripe]

2. Add to INSTALLED_APPS::

    INSTALLED_APPS = [
        # ... your apps
        'wagtail_subscriptions',
    ]

3. Configure settings::

    WAGTAIL_SUBSCRIPTIONS = {
        'PAYMENT_PROCESSORS': {
            'stripe': {
                'public_key': 'pk_test_...',
                'secret_key': 'sk_test_...',
                'webhook_secret': 'whsec_...',
            }
        },
    }

4. Run migrations::

    python manage.py migrate

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`