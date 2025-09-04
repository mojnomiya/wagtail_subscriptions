from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ..models import Subscription
from .tenant_manager import TenantSubscriptionManager


def subscription_required(view_func=None, *, redirect_url='/pricing/'):
    """Decorator to require an active subscription (works in both single/multi-tenant modes)"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            plan = TenantSubscriptionManager.get_active_plan(request)
            if not plan:
                messages.warning(request, _('An active subscription is required to access this feature.'))
                return redirect(redirect_url)
            request.subscription_plan = plan
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def feature_required(feature_slug, redirect_url='/pricing/'):
    """Decorator to require access to a specific feature (works in both single/multi-tenant modes)"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not TenantSubscriptionManager.has_feature_access(request, feature_slug):
                messages.warning(
                    request, 
                    _('Your current subscription plan does not include access to this feature.')
                )
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator