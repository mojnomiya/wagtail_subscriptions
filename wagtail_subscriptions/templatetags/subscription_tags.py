from django import template
from django.template.loader import render_to_string
from ..models import SubscriptionPlan

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
def has_feature(subscription, feature_slug):
    """Check if subscription has access to feature"""
    if not subscription:
        return False
    return subscription.has_feature_access(feature_slug)