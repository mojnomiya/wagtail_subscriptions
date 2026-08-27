from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .models import UsageRecord


def get_billing_period_days(billing_period: str) -> int:
    """Get the number of days in a billing period"""
    if billing_period == "monthly":
        return 30
    elif billing_period == "quarterly":
        return 90
    elif billing_period == "yearly":
        return 365
    elif billing_period == "lifetime":
        return 365 * 10  # 10-year approximation
    return 30


def track_feature_usage(subscription, feature_slug, count=1):
    """Track usage of a feature for quota management"""
    # Validate feature_slug to prevent injection
    if (
        not feature_slug
        or not isinstance(feature_slug, str)
        or "/" in feature_slug
        or ".." in feature_slug
    ):
        return None

    try:
        feature = subscription.plan.plan_features.get(
            feature__slug=feature_slug, is_included=True
        ).feature

        # Get current billing period info
        billing_period = subscription.plan.billing_period
        period_start = subscription.current_period_start
        period_end = subscription.current_period_end

        # Get or create usage record
        usage_record, created = UsageRecord.objects.get_or_create(
            subscription=subscription,
            feature=feature,
            period_start=period_start,
            defaults={"period_end": period_end, "usage_count": 0},
        )

        usage_record.usage_count += count
        usage_record.save()

        return usage_record

    except Exception:
        return None


def check_feature_quota(subscription, feature_slug):
    """Check if user has exceeded feature quota"""
    # Validate feature_slug to prevent injection
    if (
        not feature_slug
        or not isinstance(feature_slug, str)
        or "/" in feature_slug
        or ".." in feature_slug
    ):
        return False

    try:
        plan_feature = subscription.plan.plan_features.get(
            feature__slug=feature_slug, is_included=True
        )

        if plan_feature.feature.feature_type != "quota":
            return True  # No quota limit

        quota = plan_feature.effective_quota
        if not quota:
            return True  # Unlimited

        # Get current usage for current period
        usage_record = UsageRecord.objects.filter(
            subscription=subscription,
            feature=plan_feature.feature,
            period_start=subscription.current_period_start,
        ).first()

        current_usage = usage_record.usage_count if usage_record else 0
        return current_usage < quota

    except Exception:
        return False


def reset_feature_usage_for_period(subscription):
    """Reset usage records for a new billing period"""
    from .models import UsageRecord

    period_start = subscription.current_period_start

    UsageRecord.objects.filter(
        subscription=subscription,
        period_start__lt=period_start,
    ).delete()

    # Get all included quota features and create fresh usage records
    for plan_feature in subscription.plan.plan_features.filter(
        is_included=True, feature__feature_type="quota"
    ):
        UsageRecord.objects.get_or_create(
            subscription=subscription,
            feature=plan_feature.feature,
            period_start=period_start,
            defaults={
                "period_end": subscription.current_period_end,
                "usage_count": 0,
            },
        )


def calculate_proration(old_plan, new_plan, days_remaining):
    """Calculate proration amount for plan changes"""
    if old_plan.billing_period != new_plan.billing_period:
        # Handle cross-billing-period proration
        return _calculate_cross_period_proration(old_plan, new_plan, days_remaining)

    # Calculate daily rates
    days_in_period = get_billing_period_days(old_plan.billing_period)
    old_daily_rate = Decimal(str(old_plan.price)) / Decimal(days_in_period)
    new_daily_rate = Decimal(str(new_plan.price)) / Decimal(days_in_period)

    # Calculate proration
    unused_amount = old_daily_rate * days_remaining
    new_amount = new_daily_rate * days_remaining

    return new_amount - unused_amount


def _calculate_cross_period_proration(old_plan, new_plan, days_remaining):
    """Calculate proration when changing between different billing periods"""
    # Calculate remaining value in old plan
    old_days_in_period = get_billing_period_days(old_plan.billing_period)
    old_daily_rate = Decimal(str(old_plan.price)) / Decimal(old_days_in_period)
    old_unused = old_daily_rate * days_remaining

    # Calculate cost of equivalent period in new plan
    new_days_in_period = get_billing_period_days(new_plan.billing_period)
    new_daily_rate = Decimal(str(new_plan.price)) / Decimal(new_days_in_period)
    new_cost = new_daily_rate * days_remaining

    return new_cost - old_unused
