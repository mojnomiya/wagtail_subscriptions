from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ..models import Subscription
from .tenant_manager import TenantSubscriptionManager


class SubscriptionRequiredMixin:
    """Mixin to require an active subscription (works in both single/multi-tenant modes)"""
    subscription_redirect_url = '/subscriptions/pricing/'
    
    def dispatch(self, request, *args, **kwargs):
        plan = TenantSubscriptionManager.get_active_plan(request)
        if not plan:
            messages.warning(request, _('An active subscription is required to access this feature.'))
            return redirect(self.subscription_redirect_url)
        
        request.subscription_plan = plan
        return super().dispatch(request, *args, **kwargs)


class FeatureRequiredMixin:
    """Mixin to require access to a specific feature (works in both single/multi-tenant modes)"""
    required_feature = None
    subscription_redirect_url = '/subscriptions/pricing/'
    
    def dispatch(self, request, *args, **kwargs):
        if self.required_feature and not TenantSubscriptionManager.has_feature_access(request, self.required_feature):
            messages.warning(
                request,
                _('Your current subscription plan does not include access to this feature.')
            )
            return redirect(self.subscription_redirect_url)
        
        return super().dispatch(request, *args, **kwargs)


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