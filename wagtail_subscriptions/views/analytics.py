from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from ..analytics import SubscriptionAnalytics


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