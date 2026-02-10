# Quick Start Guide

## Test the Package in 5 Minutes

### 1. Set up the example project:

```bash
cd wagtail-subscriptions/example_project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the basic test:

```bash
python test_basic.py
```

Expected output:
```
🚀 Starting wagtail-subscriptions basic tests...
🧪 Testing model creation...
✅ Created plan: Pro Plan - $29.99/monthly
✅ Created module: Analytics Module
✅ Created feature: Analytics Module - Advanced Reports
✅ Linked feature to plan: Pro Plan - Advanced Reports
💳 Testing payment processor...
✅ Stripe processor initialized: StripePaymentProcessor
✅ Paddle processor initialized: PaddlePaymentProcessor
👤 Testing user subscription...
✅ Created user: testuser
✅ Customer auto-created: testuser
🔐 Testing permissions...
✅ Permission decorators imported successfully
🎉 All basic tests passed!
```

### 3. Run the web interface:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 4. Test in browser:

- Admin: http://127.0.0.1:8000/admin/
- Pricing: http://127.0.0.1:8000/subscriptions/pricing/

## Integration with Your Project

### Method 1: Development Install

```bash
pip install -e /path/to/wagtail-subscriptions
```

### Method 2: Direct Path

Add to your Django settings:

```python
import sys
sys.path.insert(0, '/path/to/wagtail-subscriptions')

INSTALLED_APPS = [
    # ... your apps
    'wagtail_subscriptions',
]
```

### Method 3: Copy Package

```bash
cp -r wagtail-subscriptions/wagtail_subscriptions /path/to/your/project/
```

## Verify Installation

```python
# In Django shell: python manage.py shell
from wagtail_subscriptions.models import SubscriptionPlan
print("✅ Package installed successfully!")
```

That's it! The package is ready to use.