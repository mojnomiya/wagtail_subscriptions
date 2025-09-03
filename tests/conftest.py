import pytest
from django.contrib.auth import get_user_model
from wagtail_subscriptions.models import SubscriptionPlan, Module, Feature, Subscription, Customer

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def customer(user):
    return Customer.objects.create(
        user=user,
        billing_email=user.email
    )


@pytest.fixture
def module():
    return Module.objects.create(
        name='Test Module',
        slug='test-module'
    )


@pytest.fixture
def feature(module):
    return Feature.objects.create(
        module=module,
        name='Test Feature',
        slug='test-feature'
    )


@pytest.fixture
def plan():
    return SubscriptionPlan.objects.create(
        name='Test Plan',
        slug='test-plan',
        price=29.99,
        billing_period='monthly'
    )


@pytest.fixture
def subscription(user, plan):
    return Subscription.objects.create(
        user=user,
        plan=plan,
        status='active',
        current_period_start='2024-01-01T00:00:00Z',
        current_period_end='2024-02-01T00:00:00Z'
    )