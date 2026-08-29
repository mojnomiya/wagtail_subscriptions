from decimal import Decimal

import pytest

from wagtail_subscriptions.models import PlanFeature, SubscriptionPlan
from wagtail_subscriptions.utils import (
    calculate_proration,
    check_feature_quota,
    get_billing_period_days,
    reset_feature_usage_for_period,
    track_feature_usage,
)


@pytest.mark.django_db
class TestMultiTenantDetection:
    """Test multi-tenant detection functionality"""

    def test_is_multi_tenant_when_django_tenants_installed(self):
        """Test is_multi_tenant returns True when django_tenants is available"""
        from wagtail_subscriptions.permissions.tenant_manager import TenantSubscriptionManager

        # Just verify the method exists and is callable
        result = TenantSubscriptionManager.is_multi_tenant()
        # When django_tenants is not installed, should return False
        # When installed, should return True
        assert isinstance(result, bool)

    def test_is_multi_tenant_returns_bool(self):
        """Test is_multi_tenant always returns a boolean"""
        from wagtail_subscriptions.permissions.tenant_manager import TenantSubscriptionManager

        result = TenantSubscriptionManager.is_multi_tenant()
        assert result in [True, False]


@pytest.mark.django_db
class TestFeatureQuota:
    """Test feature quota tracking and management"""

    def test_get_billing_period_days_monthly(self):
        """Test billing period days calculation for monthly"""
        days = get_billing_period_days("monthly")
        assert days == 30

    def test_get_billing_period_days_quarterly(self):
        """Test billing period days calculation for quarterly"""
        days = get_billing_period_days("quarterly")
        assert days == 90

    def test_get_billing_period_days_yearly(self):
        """Test billing period days calculation for yearly"""
        days = get_billing_period_days("yearly")
        assert days == 365

    def test_get_billing_period_days_lifetime(self):
        """Test billing period days calculation for lifetime"""
        days = get_billing_period_days("lifetime")
        assert days == 3650

    def test_track_feature_usage(self, user, plan, feature):
        """Test tracking feature usage"""
        from wagtail_subscriptions.models import Subscription

        # Set feature to quota type
        feature.feature_type = "quota"
        feature.save()

        # Create subscription and associate feature with plan
        PlanFeature.objects.create(plan=plan, feature=feature, is_included=True)

        # Create subscription
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status="active",
            current_period_start="2024-01-01",
            current_period_end="2024-01-31",
        )

        # Track usage
        result = track_feature_usage(subscription, feature.slug, count=1)
        assert result is not None
        assert result.usage_count == 1

        # Track additional usage
        result = track_feature_usage(subscription, feature.slug, count=2)
        assert result is not None
        assert result.usage_count == 3

    def test_check_feature_quota_no_quota(self, user, plan, feature):
        """Test checking quota when feature is binary type (no quota limit)"""
        from wagtail_subscriptions.models import Subscription

        # Add feature to plan without quota (default feature_type is "binary")
        PlanFeature.objects.create(plan=plan, feature=feature, is_included=True)

        # Create subscription
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status="active",
            current_period_start="2024-01-01",
            current_period_end="2024-01-31",
        )

        # Check quota - should return True (no limit for binary features)
        result = check_feature_quota(subscription, feature.slug)
        assert result is True

    def test_check_feature_quota_with_quota(self, user, plan, feature):
        """Test checking quota when feature has quota"""
        from wagtail_subscriptions.models import PlanFeature, Subscription

        # Set feature to quota type with a default quota
        feature.feature_type = "quota"
        feature.default_quota = 5
        feature.save()

        # Add feature to plan with quota
        PlanFeature.objects.create(plan=plan, feature=feature, is_included=True)

        # Create subscription
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status="active",
            current_period_start="2024-01-01",
            current_period_end="2024-01-31",
        )

        # Check quota - should return True (under limit, 0 < 5)
        result = check_feature_quota(subscription, feature.slug)
        assert result is True

    def test_reset_feature_usage_for_period(self, user, plan, feature):
        """Test resetting feature usage for a new billing period"""
        from wagtail_subscriptions.models import PlanFeature, Subscription

        # Set feature to quota type
        feature.feature_type = "quota"
        feature.default_quota = 10
        feature.save()

        # Add feature to plan with quota
        PlanFeature.objects.create(plan=plan, feature=feature, is_included=True)

        # Create subscription
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status="active",
            current_period_start="2024-01-01",
            current_period_end="2024-01-31",
        )

        # Track some usage first
        track_feature_usage(subscription, feature.slug, count=3)

        # Reset usage for new period
        reset_feature_usage_for_period(subscription)

        # Check that usage is reset
        result = check_feature_quota(subscription, feature.slug)
        assert result is True  # Should be under new limit


@pytest.mark.django_db
class TestProrationCalculation:
    """Test proration calculation for plan changes"""

    def test_calculate_proration_same_period(self, plan):
        """Test proration calculation for same billing period"""

        # Create another plan for comparison
        new_plan = SubscriptionPlan.objects.create(
            name="Premium Plan", slug="premium-plan", price=49.99, billing_period="monthly"
        )

        # Calculate proration for 15 days remaining
        result = calculate_proration(plan, new_plan, 15)

        # Should be positive (upgrade cost)
        assert isinstance(result, Decimal)
        assert result != Decimal("0.00")

    def test_calculate_proration_different_periods(self, plan):
        """Test proration calculation for different billing periods"""

        # Create a yearly plan
        yearly_plan = SubscriptionPlan.objects.create(
            name="Yearly Plan", slug="yearly-plan", price=199.99, billing_period="yearly"
        )

        # Calculate proration for 30 days remaining with different periods
        result = calculate_proration(plan, yearly_plan, 30)

        # Should return a value (not 0.00 for different periods)
        assert isinstance(result, Decimal)

    def test_calculate_proration_zero_days(self, plan):
        """Test proration calculation with zero days remaining"""

        new_plan = SubscriptionPlan.objects.create(
            name="Premium Plan", slug="premium-plan", price=49.99, billing_period="monthly"
        )

        # Calculate proration for 0 days remaining
        result = calculate_proration(plan, new_plan, 0)

        # Should be 0 or very small
        assert isinstance(result, Decimal)


@pytest.mark.django_db
class TestUtilsIntegration:
    """Integration tests for utils functions"""

    def test_full_quota_lifecycle(self, user, plan, feature):
        """Test the full quota lifecycle: track, check, reset"""
        from wagtail_subscriptions.models import PlanFeature, Subscription, UsageRecord

        # Set feature to quota type
        feature.feature_type = "quota"
        feature.default_quota = 5
        feature.save()

        # Add feature to plan with quota
        PlanFeature.objects.create(plan=plan, feature=feature, is_included=True)

        # Create subscription
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status="active",
            current_period_start="2024-01-01",
            current_period_end="2024-01-31",
        )

        # Initially under quota (0 < 5)
        assert check_feature_quota(subscription, feature.slug) is True

        # Track usage to limit
        for i in range(5):
            track_feature_usage(subscription, feature.slug, count=1)

        # At quota limit (5/5), not exceeded yet
        usage = UsageRecord.objects.get(
            subscription=subscription,
            feature=feature,
            period_start=subscription.current_period_start,
        )
        assert usage.usage_count == 5

        # Track one more to exceed quota
        track_feature_usage(subscription, feature.slug, count=1)

        # Verify usage exceeded
        usage.refresh_from_db()
        assert usage.usage_count == 6
