from decimal import Decimal
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, Payment, UsageRecord


class SubscriptionAnalytics:
    """Analytics for subscription metrics"""
    
    @staticmethod
    def get_mrr():
        """Calculate Monthly Recurring Revenue"""
        active_subs = Subscription.objects.filter(status__in=['active', 'trialing'])
        monthly_revenue = Decimal('0.00')
        
        for sub in active_subs:
            if sub.plan.billing_period == 'monthly':
                monthly_revenue += sub.plan.price
            elif sub.plan.billing_period == 'yearly':
                monthly_revenue += sub.plan.price / 12
            elif sub.plan.billing_period == 'quarterly':
                monthly_revenue += sub.plan.price / 3
        
        return monthly_revenue
    
    @staticmethod
    def get_churn_rate(days=30):
        """Calculate churn rate for the last N days"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        total_start = Subscription.objects.filter(created_at__lt=start_date).count()
        churned = Subscription.objects.filter(
            canceled_at__gte=start_date,
            canceled_at__lt=end_date
        ).count()
        
        return (churned / total_start * 100) if total_start > 0 else 0
    
    @staticmethod
    def get_conversion_rate(days=30):
        """Calculate trial to paid conversion rate"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        trials = Subscription.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            trial_end__isnull=False
        ).count()
        
        conversions = Subscription.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            trial_end__isnull=False,
            status='active'
        ).count()
        
        return (conversions / trials * 100) if trials > 0 else 0
    
    @staticmethod
    def get_feature_usage(feature_slug, days=30):
        """Get feature usage statistics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        usage = UsageRecord.objects.filter(
            feature__slug=feature_slug,
            period_start__gte=start_date
        ).aggregate(
            total_usage=Sum('usage_count'),
            avg_usage=Avg('usage_count'),
            unique_users=Count('subscription__user', distinct=True)
        )
        
        return usage