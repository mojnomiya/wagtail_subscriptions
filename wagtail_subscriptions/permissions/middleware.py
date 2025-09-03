from django.utils.deprecation import MiddlewareMixin
from ..models import Subscription


class SubscriptionMiddleware(MiddlewareMixin):
    """Middleware to add subscription information to request"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                subscription = Subscription.objects.select_related('plan').get(
                    user=request.user,
                    status__in=['trialing', 'active']
                )
                request.subscription = subscription
            except Subscription.DoesNotExist:
                request.subscription = None
        else:
            request.subscription = None
        
        return None