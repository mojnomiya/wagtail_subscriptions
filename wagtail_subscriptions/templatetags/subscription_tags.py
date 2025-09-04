from django import template
from django.template.loader import render_to_string
from ..models import SubscriptionPlan
from ..permissions.tenant_manager import TenantSubscriptionManager

register = template.Library()


@register.inclusion_tag('wagtail_subscriptions/components/price_table.html', takes_context=True)
def price_table(context, plans=None, show_trial=True, highlight_plan=None):
    """
    Render subscription pricing table
    
    Usage:
    {% load subscription_tags %}
    {% price_table %}
    {% price_table plans=custom_plans show_trial=False %}
    {% price_table highlight_plan="pro-plan" %}
    """
    if plans is None:
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price')
    
    return {
        'plans': plans,
        'show_trial': show_trial,
        'highlight_plan': highlight_plan,
        'request': context.get('request'),
        'user': context.get('user'),
    }


@register.simple_tag
def plan_features(plan):
    """Get features for a plan"""
    return plan.plan_features.filter(is_included=True, feature__is_active=True)


@register.filter
def has_feature(request, feature_slug):
    """Check if current context has access to feature (works in both single/multi-tenant modes)"""
    if not request:
        return False
    return TenantSubscriptionManager.has_feature_access(request, feature_slug)

@register.simple_tag(takes_context=True)
def subscription_info(context):
    """Get subscription information for current context"""
    request = context.get('request')
    if not request:
        return None
    return TenantSubscriptionManager.get_subscriber_info(request)

@register.inclusion_tag('wagtail_subscriptions/components/pricing_cards.html', takes_context=True)
def pricing_cards(context):
    """Render pricing cards component"""
    return {
        'request': context.get('request'),
    }