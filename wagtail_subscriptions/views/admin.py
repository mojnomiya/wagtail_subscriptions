from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ..models import SubscriptionPlan, Module, Feature, Subscription, Customer
from ..analytics import SubscriptionAnalytics
from ..permissions.mixins import AdminSubscriptionMixin


class SubscriptionDashboardView(AdminSubscriptionMixin, TemplateView):
    template_name = 'wagtail_subscriptions/admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_subscriptions': Subscription.objects.filter(status__in=['active', 'trialing']).count(),
            'total_plans': SubscriptionPlan.objects.filter(is_active=True).count(),
            'total_customers': Customer.objects.count(),
            'mrr': SubscriptionAnalytics.get_mrr(),
            'recent_subscriptions': Subscription.objects.order_by('-created_at')[:5],
            'breadcrumb_items': [
                {"url": "/admin/", "label": _("Home")},
                {"url": None, "label": _("Subscriptions")},
                {"url": None, "label": _("Dashboard")}
            ]
        })
        return context


class PlansManagementView(AdminSubscriptionMixin, TemplateView):
    template_name = 'wagtail_subscriptions/admin/plans.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = SubscriptionPlan.objects.all().order_by('sort_order')
        return context


class FeaturesManagementView(AdminSubscriptionMixin, TemplateView):
    template_name = 'wagtail_subscriptions/admin/features.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modules'] = Module.objects.all().order_by('sort_order')
        context['features'] = Feature.objects.all().order_by('module', 'sort_order')
        return context


class CustomersManagementView(AdminSubscriptionMixin, TemplateView):
    template_name = 'wagtail_subscriptions/admin/customers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.select_related('user').order_by('-created_at')
        return context


class SettingsView(AdminSubscriptionMixin, TemplateView):
    template_name = 'wagtail_subscriptions/admin/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.conf import settings
        from ..forms import PaymentProcessorConfigForm
        
        context['payment_processors'] = getattr(settings, 'WAGTAIL_SUBSCRIPTIONS', {}).get('PAYMENT_PROCESSORS', {})
        context['config_form'] = PaymentProcessorConfigForm()
        context['show_config_guide'] = True
        return context
    
    def post(self, request, *args, **kwargs):
        from ..forms import PaymentProcessorConfigForm
        form = PaymentProcessorConfigForm(request.POST)
        
        if form.is_valid():
            messages.success(request, _('Configuration guide updated. Please update your Django settings file.'))
        else:
            messages.error(request, _('Please correct the errors below.'))
        
        return self.get(request, *args, **kwargs)