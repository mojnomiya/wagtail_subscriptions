from django.http import JsonResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from ..permissions.mixins import SubscriptionRequiredMixin
from ..models import SubscriptionPlan


class SubscriptionAPIView(SubscriptionRequiredMixin, View):
    """API endpoint for subscription information"""
    
    def get(self, request, *args, **kwargs):
        """Return subscription details as JSON"""
        subscription = self.subscription
        
        data = {
            'plan': {
                'name': subscription.plan.name,
                'slug': subscription.plan.slug,
                'price': float(subscription.plan.price),
                'billing_period': subscription.plan.billing_period,
            },
            'status': subscription.status,
            'is_active': subscription.is_active,
            'is_trial': subscription.is_trial,
            'current_period_start': subscription.current_period_start.isoformat(),
            'current_period_end': subscription.current_period_end.isoformat(),
            'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
            'features': list(subscription.plan.plan_features.filter(
                is_included=True,
                feature__is_active=True
            ).values_list('feature__slug', flat=True))
        }
        
        return JsonResponse(data)


class PricingPlansAPIView(View):
    """Public API endpoint for pricing plans"""
    
    def get(self, request, *args, **kwargs):
        """Return all active pricing plans as JSON"""
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price')
        
        plans_data = []
        for plan in plans:
            # Get features for display
            features = []
            for plan_feature in plan.plan_features.filter(is_included=True, feature__is_active=True):
                feature_text = plan_feature.feature.name
                if plan_feature.feature.feature_type == 'quota' and plan_feature.effective_quota:
                    feature_text += f" ({plan_feature.effective_quota} {plan_feature.feature.quota_unit})"
                features.append(feature_text)
            
            plans_data.append({
                'slug': plan.slug,
                'name': plan.name,
                'description': plan.description,
                'price': float(plan.price),
                'billing_period': plan.billing_period,
                'billing_period_display': plan.get_billing_period_display(),
                'trial_period_days': plan.trial_period_days,
                'is_active': plan.is_active,
                'sort_order': plan.sort_order,
                'features': features,
                'created_at': plan.created_at.isoformat() if plan.created_at else None,
            })
        
        return JsonResponse({
            'plans': plans_data,
            'success': True,
            'count': len(plans_data)
        })