from django.views.generic import TemplateView
from ..models import SubscriptionPlan, Module


class PricingView(TemplateView):
    """Display pricing plans and features"""
    template_name = 'wagtail_subscriptions/pricing/pricing_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
        context['modules'] = Module.objects.filter(is_active=True).prefetch_related('features').order_by('sort_order')
        return context