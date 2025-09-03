from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ..models import SubscriptionPlan, Subscription, Customer
from ..payments import get_payment_processor
from ..permissions.mixins import SubscriptionRequiredMixin


class SubscribeView(LoginRequiredMixin, TemplateView):
    """Handle subscription creation"""
    template_name = 'wagtail_subscriptions/subscription/subscribe.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = get_object_or_404(SubscriptionPlan, slug=kwargs['plan_slug'], is_active=True)
        context['plan'] = plan
        return context
    
    def post(self, request, *args, **kwargs):
        plan = get_object_or_404(SubscriptionPlan, slug=kwargs['plan_slug'], is_active=True)
        
        # Get or create customer
        customer, created = Customer.objects.get_or_create(user=request.user)
        
        try:
            # Create subscription via payment processor
            processor = get_payment_processor()
            
            if not customer.stripe_customer_id:
                customer.stripe_customer_id = processor.create_customer(request.user)
                customer.save()
            
            subscription_data = processor.create_subscription(
                customer.stripe_customer_id,
                plan.slug,  # Assuming plan slug matches Stripe price ID
                trial_period_days=plan.trial_period_days
            )
            
            # Create local subscription record
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                status=subscription_data['status'],
                external_id=subscription_data['id'],
                current_period_start=subscription_data['current_period_start'],
                current_period_end=subscription_data['current_period_end'],
                trial_end=subscription_data.get('trial_end'),
            )
            
            messages.success(request, _('Successfully subscribed to {}!').format(plan.name))
            return redirect('wagtail_subscriptions:customer_portal')
            
        except Exception as e:
            messages.error(request, _('Failed to create subscription: {}').format(str(e)))
            return self.get(request, *args, **kwargs)


class CustomerPortalView(SubscriptionRequiredMixin, TemplateView):
    """Customer self-service portal"""
    template_name = 'wagtail_subscriptions/subscription/portal.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscription'] = self.subscription
        context['available_plans'] = SubscriptionPlan.objects.filter(is_active=True).exclude(id=self.subscription.plan.id)
        return context