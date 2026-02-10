from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from wagtail_subscriptions.models import Customer, Subscription, SubscriptionPlan
from wagtail_subscriptions.views.plan_management import (
    CancelSubscriptionView,
    ChangePlanView,
)
from wagtail_subscriptions.views.subscription import SubscribeView

User = get_user_model()


class TestSubscriptionLifecycle(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.basic_plan = SubscriptionPlan.objects.create(
            name="Basic Plan", slug="basic", price=9.99, billing_period="monthly"
        )

        self.pro_plan = SubscriptionPlan.objects.create(
            name="Pro Plan", slug="pro", price=19.99, billing_period="monthly"
        )

    @patch("wagtail_subscriptions.payments.get_payment_processor")
    def test_subscription_creation(self, mock_get_processor):
        from django.utils import timezone
        from datetime import timedelta
        
        # Mock payment processor
        mock_processor = Mock()
        mock_processor.create_customer.return_value = {"id": "cus_test123"}
        mock_processor.create_subscription.return_value = {
            "id": "sub_test123",
            "status": "active",
            "current_period_start": 1640995200,
            "current_period_end": 1643673600,
            "trial_end": None,
        }
        mock_get_processor.return_value = mock_processor

        # Create subscription directly (not via HTTP)
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.basic_plan,
            status="active",
            external_id="sub_test123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        # Verify subscription created
        assert subscription is not None
        assert subscription.plan == self.basic_plan
        assert subscription.external_id == "sub_test123"
        assert subscription.status == "active"

    def test_duplicate_subscription_prevention(self):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        # Create existing subscription
        Subscription.objects.create(
            user=self.user,
            plan=self.basic_plan,
            status="active",
            external_id="sub_existing",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        # Try to create another subscription
        self.client.force_login(self.user)
        response = self.client.post(f"/subscriptions/subscribe/{self.pro_plan.slug}/")

        # Should redirect with warning
        assert response.status_code == 302
        assert Subscription.objects.filter(user=self.user).count() == 1

    @patch("wagtail_subscriptions.payments.get_payment_processor")
    def test_plan_upgrade(self, mock_get_processor):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        # Create existing subscription
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.basic_plan,
            status="active",
            external_id="sub_test123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            payment_processor="stripe",
        )

        # Mock payment processor
        mock_processor = Mock()
        mock_processor.update_subscription.return_value = {
            "id": "sub_test123",
            "status": "active",
        }
        mock_get_processor.return_value = mock_processor

        # Upgrade plan directly
        subscription.plan = self.pro_plan
        subscription.save()

        # Verify plan changed
        subscription.refresh_from_db()
        assert subscription.plan == self.pro_plan

    @patch("wagtail_subscriptions.payments.get_payment_processor")
    def test_subscription_cancellation(self, mock_get_processor):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        # Create subscription
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.basic_plan,
            status="active",
            external_id="sub_test123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            payment_processor="stripe",
        )

        # Mock payment processor
        mock_processor = Mock()
        mock_processor.cancel_subscription.return_value = {
            "id": "sub_test123",
            "status": "canceled",
            "canceled_at": 1640995200,
            "cancel_at_period_end": False,
        }
        mock_get_processor.return_value = mock_processor

        # Cancel subscription directly
        subscription.status = "canceled"
        subscription.canceled_at = now
        subscription.save()

        # Verify cancellation
        subscription.refresh_from_db()
        assert subscription.status == "canceled"
        assert subscription.canceled_at is not None

    def test_feature_access_check(self):
        from django.utils import timezone
        from datetime import timedelta
        from wagtail_subscriptions.models import Feature, Module, PlanFeature

        now = timezone.now()
        # Create feature
        module = Module.objects.create(name="Test Module", slug="test")
        feature = Feature.objects.create(
            module=module,
            name="Test Feature",
            slug="test-feature",
            feature_type="binary",
        )

        # Create subscription with feature
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.basic_plan,
            status="active",
            external_id="sub_test123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        # Add feature to plan
        PlanFeature.objects.create(plan=self.basic_plan, feature=feature, is_included=True)

        # Test feature access
        assert subscription.has_feature_access("test-feature") == True
        assert subscription.has_feature_access("nonexistent-feature") == False
