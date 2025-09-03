from django.http import JsonResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from ..permissions.mixins import SubscriptionRequiredMixin


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