from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ..models import Subscription


class SubscriptionRequiredMixin(LoginRequiredMixin):
    """Mixin to require an active subscription"""
    subscription_redirect_url = '/subscriptions/pricing/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        try:
            subscription = Subscription.objects.get(
                user=request.user,
                status__in=['trialing', 'active']
            )
            request.subscription = subscription
        except Subscription.DoesNotExist:
            messages.warning(request, _('An active subscription is required to access this feature.'))
            return redirect(self.subscription_redirect_url)
        
        return super().dispatch(request, *args, **kwargs)


class FeatureRequiredMixin(SubscriptionRequiredMixin):
    """Mixin to require access to a specific feature"""
    required_feature = None
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        if hasattr(request, 'subscription') and self.required_feature:
            if not request.subscription.has_feature_access(self.required_feature):
                messages.warning(
                    request,
                    _('Your current subscription plan does not include access to this feature.')
                )
                return redirect(self.subscription_redirect_url)
        
        return response


class AdminSubscriptionMixin:
    """Mixin for admin views to check subscription management permissions"""
    
    def has_permission(self, request):
        return (
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request):
            messages.error(request, _('You do not have permission to access this area.'))
            return redirect('/admin/')
        return super().dispatch(request, *args, **kwargs)