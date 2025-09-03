from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from ..analytics import SubscriptionAnalytics
from ..models import Subscription, SubscriptionPlan


@method_decorator(staff_member_required, name='dispatch')
class AnalyticsDashboardView(TemplateView):
    """Analytics dashboard for subscription metrics"""
    template_name = 'wagtail_subscriptions/admin/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'mrr': SubscriptionAnalytics.get_mrr(),
            'churn_rate': SubscriptionAnalytics.get_churn_rate(),
            'conversion_rate': SubscriptionAnalytics.get_conversion_rate(),
            'total_subscriptions': Subscription.objects.filter(status__in=['active', 'trialing']).count(),
            'total_plans': SubscriptionPlan.objects.filter(is_active=True).count(),
        })
        
        return context


@method_decorator(staff_member_required, name='dispatch')
class AnalyticsAPIView(TemplateView):
    """API endpoint for analytics data"""
    
    def get(self, request, *args, **kwargs):
        metric = request.GET.get('metric')
        days = int(request.GET.get('days', 30))
        
        if metric == 'mrr':
            data = {'value': float(SubscriptionAnalytics.get_mrr())}
        elif metric == 'churn':
            data = {'value': SubscriptionAnalytics.get_churn_rate(days)}
        elif metric == 'conversion':
            data = {'value': SubscriptionAnalytics.get_conversion_rate(days)}
        else:
            data = {'error': 'Invalid metric'}
        
        return JsonResponse(data)