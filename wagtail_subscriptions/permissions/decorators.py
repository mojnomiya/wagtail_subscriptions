from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ..models import Subscription


def subscription_required(view_func=None, *, redirect_url='/pricing/'):
    """Decorator to require an active subscription"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            try:
                subscription = Subscription.objects.get(
                    user=request.user,
                    status__in=['trialing', 'active']
                )
                request.subscription = subscription
                return view_func(request, *args, **kwargs)
            except Subscription.DoesNotExist:
                messages.warning(request, _('An active subscription is required to access this feature.'))
                return redirect(redirect_url)
        return _wrapped_view
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def feature_required(feature_slug, redirect_url='/pricing/'):
    """Decorator to require access to a specific feature"""
    def decorator(view_func):
        @wraps(view_func)
        @subscription_required
        def _wrapped_view(request, *args, **kwargs):
            if request.subscription.has_feature_access(feature_slug):
                return view_func(request, *args, **kwargs)
            else:
                messages.warning(
                    request, 
                    _('Your current subscription plan does not include access to this feature.')
                )
                return redirect(redirect_url)
        return _wrapped_view
    return decorator