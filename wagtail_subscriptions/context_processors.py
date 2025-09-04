from .permissions.tenant_manager import TenantSubscriptionManager


def subscription_context(request):
    """Add subscription context to all templates"""
    return {
        'subscription_info': TenantSubscriptionManager.get_subscriber_info(request),
        'is_multi_tenant': TenantSubscriptionManager.is_multi_tenant(),
        'current_plan': TenantSubscriptionManager.get_active_plan(request),
    }