Wagtail Subscriptions Documentation
===================================

A comprehensive subscription management package for Wagtail CMS that enables SaaS businesses to manage subscription plans, features, permissions, and payment integrations seamlessly within their Wagtail admin interface.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started:

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts:

   architecture
   api-reference

.. toctree::
   :maxdepth: 2
   :caption: Integration Guides:

   payment-integration
   multi-tenant
   deployment

.. toctree::
   :maxdepth: 2
   :caption: Development:

   CONTRIBUTING
   TEST_GUIDE

Features
--------

* **Subscription Plan Management**: Visual plan builder with flexible pricing models
* **Feature System**: Hierarchical feature organization with usage quotas
* **Payment Integration**: Multi-provider support (Stripe, Paddle, PayPal)
* **Permission Control**: Django permission integration with subscription-based access
* **Multi-Tenant Support**: Automatic detection and support for django-tenant-schemas
* **Wagtail Integration**: Native admin interface and content integration
* **Customer Portal**: Self-service subscription management
* **Analytics**: Built-in reporting and usage tracking
* **Audit Logging**: Complete audit trail for compliance

Quick Start
-----------

1. Install the package::

    pip install wagtail-subscriptions

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
    python manage.py setup_subscription_permissions

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`