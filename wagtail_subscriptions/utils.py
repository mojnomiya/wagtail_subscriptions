from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from .models import UsageRecord, Subscription


def track_feature_usage(subscription, feature_slug, count=1):
    """Track usage of a feature for quota management"""
    try:
        feature = subscription.plan.plan_features.get(
            feature__slug=feature_slug,
            is_included=True
        ).feature
        
        # Get current billing period
        now = timezone.now()
        period_start = subscription.current_period_start
        period_end = subscription.current_period_end
        
        # Get or create usage record
        usage_record, created = UsageRecord.objects.get_or_create(
            subscription=subscription,
            feature=feature,
            period_start=period_start,
            defaults={
                'period_end': period_end,
                'usage_count': 0
            }
        )
        
        usage_record.usage_count += count
        usage_record.save()
        
        return usage_record
        
    except Exception:
        return None


def check_feature_quota(subscription, feature_slug):
    """Check if user has exceeded feature quota"""
    try:
        plan_feature = subscription.plan.plan_features.get(
            feature__slug=feature_slug,
            is_included=True
        )
        
        if plan_feature.feature.feature_type != 'quota':
            return True  # No quota limit
        
        quota = plan_feature.effective_quota
        if not quota:
            return True  # Unlimited
        
        # Get current usage
        usage_record = UsageRecord.objects.filter(
            subscription=subscription,
            feature=plan_feature.feature,
            period_start=subscription.current_period_start
        ).first()
        
        current_usage = usage_record.usage_count if usage_record else 0
        return current_usage < quota
        
    except Exception:
        return False


def calculate_proration(old_plan, new_plan, days_remaining):
    """Calculate proration amount for plan changes"""
    if old_plan.billing_period != new_plan.billing_period:
        return Decimal('0.00')  # Different billing periods
    
    # Calculate daily rates
    if old_plan.billing_period == 'monthly':
        days_in_period = 30
    elif old_plan.billing_period == 'yearly':
        days_in_period = 365
    else:
        days_in_period = 30
    
    old_daily_rate = old_plan.price / days_in_period
    new_daily_rate = new_plan.price / days_in_period
    
    # Calculate proration
    unused_amount = old_daily_rate * days_remaining
    new_amount = new_daily_rate * days_remaining
    
    return new_amount - unused_amount