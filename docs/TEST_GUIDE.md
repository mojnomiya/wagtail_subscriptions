# Testing Wagtail Subscriptions Package

This guide shows you how to test the wagtail-subscriptions package locally without publishing it.

## Method 1: Using the Example Project (Recommended)

### 1. Set up the example project:

```bash
cd wagtail-subscriptions/example_project
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../requirements-dev.txt
```

### 2. Run migrations and create superuser:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3. Start the development server:

```bash
python manage.py runserver
```

### 4. Test the package:

- Visit http://127.0.0.1:8000/admin/ (Wagtail admin)
- Visit http://127.0.0.1:8000/subscriptions/pricing/ (Pricing page)
- Create subscription plans in the admin
- Test subscription flows

## Method 2: Install in Development Mode

### 1. In your existing Django/Wagtail project:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Install the package in development mode
pip install -e /path/to/wagtail-subscriptions
```

### 2. Add to your settings.py:

```python
INSTALLED_APPS = [
    # ... your existing apps
    'wagtail_subscriptions',
]

WAGTAIL_SUBSCRIPTIONS = {
    'PAYMENT_PROCESSORS': {
        'stripe': {
            'public_key': 'pk_test_your_key',
            'secret_key': 'sk_test_your_key',
            'webhook_secret': 'whsec_your_secret',
        }
    }
}
```

### 3. Add URLs:

```python
# urls.py
urlpatterns = [
    # ... your existing URLs
    path('subscriptions/', include('wagtail_subscriptions.urls')),
]
```

### 4. Run migrations:

```bash
python manage.py migrate
```

## Method 3: Using pip install from local directory

### 1. Install directly from the package directory:

```bash
pip install /path/to/wagtail-subscriptions
```

### 2. Or with extras:

```bash
pip install /path/to/wagtail-subscriptions[stripe,dev]
```

## Method 4: Using Docker (for isolated testing)

### 1. Create a Dockerfile in the example_project:

```dockerfile
FROM python:3.10
WORKDIR /app
COPY ../requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 2. Build and run:

```bash
docker build -t wagtail-subscriptions-test .
docker run -p 8000:8000 wagtail-subscriptions-test
```

## Testing Checklist

### Basic Functionality:
- [ ] Package imports without errors
- [ ] Migrations run successfully
- [ ] Admin interfaces load
- [ ] Models can be created/edited

### Subscription Features:
- [ ] Create subscription plans
- [ ] Create modules and features
- [ ] Link features to plans
- [ ] Test permission decorators
- [ ] Test template tags

### Payment Integration:
- [ ] Configure Stripe test keys
- [ ] Test subscription creation
- [ ] Test webhook handling
- [ ] Test customer portal

### Advanced Features:
- [ ] Test analytics dashboard
- [ ] Test usage tracking
- [ ] Test feature quotas
- [ ] Test management commands

## Quick Test Script

Create a test script to verify basic functionality:

```python
# test_basic.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'example_project.settings')
django.setup()

from wagtail_subscriptions.models import SubscriptionPlan, Module, Feature

# Test model creation
plan = SubscriptionPlan.objects.create(
    name="Test Plan",
    slug="test-plan",
    price=29.99,
    billing_period="monthly"
)

module = Module.objects.create(
    name="Test Module",
    slug="test-module"
)

feature = Feature.objects.create(
    module=module,
    name="Test Feature",
    slug="test-feature"
)

print("✅ Basic models created successfully!")
print(f"Plan: {plan}")
print(f"Module: {module}")
print(f"Feature: {feature}")
```

Run with: `python test_basic.py`

## Troubleshooting

### Common Issues:

1. **Import Error**: Make sure the package is in your Python path
2. **Migration Error**: Run `python manage.py makemigrations wagtail_subscriptions` first
3. **Template Error**: Ensure templates are in the correct directory structure
4. **Static Files**: Run `python manage.py collectstatic` for production

### Debug Mode:

Enable debug logging in settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'wagtail_subscriptions': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Running Tests

### Unit Tests:
```bash
cd wagtail-subscriptions
pytest
```

### With Coverage:
```bash
pytest --cov=wagtail_subscriptions
```

### Integration Tests:
```bash
cd example_project
python manage.py test
```

This testing approach allows you to thoroughly validate the package before publishing or deploying to production.