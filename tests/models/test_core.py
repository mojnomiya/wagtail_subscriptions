import pytest
from django.core.exceptions import ValidationError
from wagtail_subscriptions.models import SubscriptionPlan, Subscription


@pytest.mark.django_db
class TestSubscriptionPlan:
    def test_create_plan(self):
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro',
            price=29.99,
            billing_period='monthly'
        )
        assert plan.name == 'Pro Plan'
        assert plan.price == 29.99
        assert str(plan) == 'Pro Plan - $29.99/monthly'

    def test_plan_ordering(self):
        plan1 = SubscriptionPlan.objects.create(name='Plan 1', slug='plan1', price=10, sort_order=2)
        plan2 = SubscriptionPlan.objects.create(name='Plan 2', slug='plan2', price=20, sort_order=1)
        
        plans = list(SubscriptionPlan.objects.all())
        assert plans[0] == plan2
        assert plans[1] == plan1


@pytest.mark.django_db
class TestSubscription:
    def test_subscription_properties(self, subscription):
        assert subscription.is_active
        assert not subscription.is_trial

    def test_feature_access(self, subscription, feature):
        subscription.plan.plan_features.create(feature=feature, is_included=True)
        assert subscription.has_feature_access('test-feature')
        assert not subscription.has_feature_access('nonexistent-feature')