from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from ..models import SubscriptionPlan, Feature, PlanFeature
from ..permissions.mixins import AdminSubscriptionMixin


class PlanFeatureManagementView(AdminSubscriptionMixin, TemplateView):
    template_name = 'wagtail_subscriptions/admin/plan_features.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        
        if plan_id:
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)
            context['plan'] = plan
            context['plan_features'] = plan.plan_features.all().select_related('feature', 'feature__module')
            context['available_features'] = Feature.objects.filter(is_active=True).exclude(
                id__in=plan.plan_features.values_list('feature_id', flat=True)
            )
        else:
            context['plans'] = SubscriptionPlan.objects.filter(is_active=True)
            context['all_plan_features'] = PlanFeature.objects.all().select_related('plan', 'feature', 'feature__module')
        
        context['breadcrumb_items'] = [
            {"url": "/admin/", "label": _("Home")},
            {"url": None, "label": _("Subscriptions")},
            {"url": None, "label": _("Plan Features")}
        ]
        return context
    
    def post(self, request, *args, **kwargs):
        plan_id = request.POST.get('plan_id')
        feature_id = request.POST.get('feature_id')
        action = request.POST.get('action')
        
        if action == 'add_feature':
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)
            feature = get_object_or_404(Feature, id=feature_id)
            
            plan_feature, created = PlanFeature.objects.get_or_create(
                plan=plan,
                feature=feature,
                defaults={'is_included': True}
            )
            
            if created:
                messages.success(request, _('Feature added to plan successfully.'))
            else:
                messages.info(request, _('Feature is already associated with this plan.'))
        
        elif action == 'remove_feature':
            plan_feature = get_object_or_404(PlanFeature, id=request.POST.get('plan_feature_id'))
            plan_feature.delete()
            messages.success(request, _('Feature removed from plan successfully.'))
        
        elif action == 'toggle_included':
            plan_feature = get_object_or_404(PlanFeature, id=request.POST.get('plan_feature_id'))
            plan_feature.is_included = not plan_feature.is_included
            plan_feature.save()
            status = _('included') if plan_feature.is_included else _('excluded')
            messages.success(request, _('Feature is now {status}.').format(status=status))
        
        return redirect(request.path)