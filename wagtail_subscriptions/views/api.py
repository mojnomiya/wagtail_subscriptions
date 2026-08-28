from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import View

from ..models import Subscription, SubscriptionPlan
from ..permissions.mixins import SubscriptionRequiredMixin


class SubscriptionAPIView(SubscriptionRequiredMixin, View):
    """API endpoint for subscription information"""

    def get(self, request, *args, **kwargs):
        """Return subscription details as JSON"""
        subscription = self.subscription

        data = {
            "plan": {
                "name": subscription.plan.name,
                "slug": subscription.plan.slug,
                "price": float(subscription.plan.price),
                "billing_period": subscription.plan.billing_period,
            },
            "status": subscription.status,
            "is_active": subscription.is_active,
            "is_trial": subscription.is_trial,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
            "features": self._get_plan_features(subscription.plan),
        }

        return JsonResponse(data)

    @staticmethod
    def _get_plan_features(plan):
        """Get features for a plan"""
        features = []
        for plan_feature in plan.plan_features.filter(
            is_included=True, feature__is_active=True
        ).select_related("feature"):
            feature_info = {
                "name": plan_feature.feature.name,
                "slug": plan_feature.feature.slug,
                "type": plan_feature.feature.feature_type,
            }
            if plan_feature.feature.feature_type == "quota" and plan_feature.effective_quota:
                feature_info["quota"] = plan_feature.effective_quota
                feature_info["unit"] = plan_feature.feature.quota_unit or ""
            features.append(feature_info)
        return features


class PricingPlansAPIView(View):
    """Public API endpoint for pricing plans"""

    def get(self, request, *args, **kwargs):
        """Return all active pricing plans as JSON"""
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by("sort_order", "price")

        plans_data = []
        for plan in plans:
            # Get features for display
            features = []
            for plan_feature in plan.plan_features.filter(
                is_included=True, feature__is_active=True
            ).select_related("feature"):
                feature_text = plan_feature.feature.name
                if plan_feature.feature.feature_type == "quota" and plan_feature.effective_quota:
                    feature_text += (
                        f" ({plan_feature.effective_quota} {plan_feature.feature.quota_unit})"
                    )
                features.append(
                    {
                        "name": plan_feature.feature.name,
                        "slug": plan_feature.feature.slug,
                        "type": plan_feature.feature.feature_type,
                        "quota": plan_feature.effective_quota,
                        "unit": plan_feature.feature.quota_unit or "",
                    }
                )

            plans_data.append(
                {
                    "slug": plan.slug,
                    "name": plan.name,
                    "description": plan.description,
                    "price": float(plan.price),
                    "billing_period": plan.billing_period,
                    "billing_period_display": plan.get_billing_period_display(),
                    "trial_period_days": plan.trial_period_days,
                    "is_active": plan.is_active,
                    "sort_order": plan.sort_order,
                    "features": features,
                    "created_at": plan.created_at.isoformat() if plan.created_at else None,
                }
            )

        return JsonResponse({"plans": plans_data, "success": True, "count": len(plans_data)})


class SubscriptionStatsAPIView(View):
    """API endpoint for subscription statistics"""

    def get(self, request, *args, **kwargs):
        """Return subscription statistics as JSON"""
        from .analytics import SubscriptionAnalytics

        days = int(request.GET.get("days", 30))

        data = {
            "mrr": float(SubscriptionAnalytics.get_mrr()),
            "churn_rate": SubscriptionAnalytics.get_churn_rate(days),
            "conversion_rate": SubscriptionAnalytics.get_conversion_rate(days),
            "active_subscriptions": Subscription.objects.filter(
                status__in=["active", "trialing"]
            ).count(),
            "total_subscriptions": Subscription.objects.count(),
        }

        return JsonResponse(data)


class FeatureUsageAPIView(View):
    """API endpoint for feature usage statistics"""

    def get(self, request, *args, **kwargs):
        """Return feature usage statistics as JSON"""
        feature_slug = request.GET.get("feature")

        if not feature_slug:
            return JsonResponse({"error": "feature parameter required"}, status=400)

        from .analytics import SubscriptionAnalytics

        days = int(request.GET.get("days", 30))
        usage = SubscriptionAnalytics.get_feature_usage(feature_slug, days)

        data = {
            "feature_slug": feature_slug,
            "total_usage": usage.get("total_usage", 0) or 0,
            "avg_usage": float(usage.get("avg_usage", 0) or 0),
            "unique_users": usage.get("unique_users", 0) or 0,
        }

        return JsonResponse(data)


class TrialStatsAPIView(View):
    """API endpoint for trial statistics"""

    def get(self, request, *args, **kwargs):
        """Return trial statistics as JSON"""
        from datetime import timedelta

        days = int(request.GET.get("days", 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        trials_data = {
            "new_trials": Subscription.objects.filter(
                created_at__gte=start_date, created_at__lt=end_date, trial_end__isnull=False
            ).count(),
            "converted_to_paid": Subscription.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                trial_end__isnull=False,
                status="active",
            ).count(),
            "expired_trials": Subscription.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                trial_end__isnull=False,
                status="canceled",
            ).count(),
            "active_trials": Subscription.objects.filter(
                status="trialing", trial_end__gte=end_date
            ).count(),
        }

        # Calculate conversion rate
        trials = trials_data["new_trials"]
        conversions = trials_data["converted_to_paid"]
        conversion_rate = (conversions / trials * 100) if trials > 0 else 0

        trials_data["conversion_rate"] = conversion_rate

        return JsonResponse(trials_data)
