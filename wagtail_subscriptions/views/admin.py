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
    template_name = "wagtail_subscriptions/admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Enhanced analytics
        from datetime import datetime, timedelta
        from django.utils import timezone
        from django.db.models import Count, Sum

        now = timezone.now()
        last_month = now - timedelta(days=30)

        # Basic metrics
        active_subs = Subscription.objects.filter(status__in=["active", "trialing"])
        total_subs = active_subs.count()

        # Growth metrics
        new_subs_this_month = Subscription.objects.filter(created_at__gte=last_month).count()
        canceled_this_month = Subscription.objects.filter(
            canceled_at__gte=last_month, canceled_at__isnull=False
        ).count()

        # Revenue metrics
        mrr = SubscriptionAnalytics.get_mrr()
        churn_rate = SubscriptionAnalytics.get_churn_rate(30)

        # Plan distribution
        plan_distribution = (
            active_subs.values("plan__name")
            .annotate(count=Count("id"), revenue=Sum("plan__price"))
            .order_by("-count")
        )

        # Recent activity
        recent_subscriptions = Subscription.objects.select_related("user", "plan").order_by(
            "-created_at"
        )[:5]
        recent_cancellations = (
            Subscription.objects.filter(canceled_at__isnull=False)
            .select_related("user", "plan")
            .order_by("-canceled_at")[:5]
        )

        context.update(
            {
                "total_subscriptions": total_subs,
                "total_plans": SubscriptionPlan.objects.filter(is_active=True).count(),
                "total_customers": Customer.objects.count(),
                "mrr": mrr,
                "new_subs_this_month": new_subs_this_month,
                "canceled_this_month": canceled_this_month,
                "churn_rate": round(churn_rate, 2),
                "plan_distribution": plan_distribution,
                "recent_subscriptions": recent_subscriptions,
                "recent_cancellations": recent_cancellations,
                "growth_rate": round(
                    (new_subs_this_month - canceled_this_month) / max(total_subs, 1) * 100,
                    2,
                ),
                "breadcrumb_items": [
                    {"url": "/admin/", "label": _("Home")},
                    {"url": None, "label": _("Subscriptions")},
                    {"url": None, "label": _("Dashboard")},
                ],
            }
        )
        return context


class PlansManagementView(AdminSubscriptionMixin, TemplateView):
    template_name = "wagtail_subscriptions/admin/plans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = SubscriptionPlan.objects.all().order_by("sort_order")
        return context


class FeaturesManagementView(AdminSubscriptionMixin, TemplateView):
    template_name = "wagtail_subscriptions/admin/features.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["modules"] = Module.objects.all().order_by("sort_order")
        context["features"] = Feature.objects.all().order_by("module", "sort_order")
        return context


class CustomersManagementView(AdminSubscriptionMixin, TemplateView):
    template_name = "wagtail_subscriptions/admin/customers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filter parameters
        status_filter = self.request.GET.get("status", "")
        plan_filter = self.request.GET.get("plan", "")
        search_query = self.request.GET.get("search", "")

        # Base queryset
        customers = Customer.objects.select_related("user").prefetch_related(
            "user__subscriptions__plan"
        )

        # Apply filters
        if search_query:
            customers = (
                customers.filter(user__email__icontains=search_query)
                | customers.filter(user__first_name__icontains=search_query)
                | customers.filter(user__last_name__icontains=search_query)
            )

        if status_filter:
            customers = customers.filter(user__subscriptions__status=status_filter)

        if plan_filter:
            customers = customers.filter(user__subscriptions__plan__slug=plan_filter)

        context.update(
            {
                "customers": customers.distinct().order_by("-created_at"),
                "status_choices": Subscription.STATUS_CHOICES,
                "plans": SubscriptionPlan.objects.filter(is_active=True),
                "current_filters": {
                    "status": status_filter,
                    "plan": plan_filter,
                    "search": search_query,
                },
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        customer_ids = request.POST.getlist("customer_ids")

        if not customer_ids:
            messages.error(request, _("No customers selected."))
            return redirect("wagtail_subscriptions_admin:customers")

        if action == "cancel_subscriptions":
            self._bulk_cancel_subscriptions(customer_ids)
        elif action == "export_customers":
            return self._export_customers(customer_ids)

        return redirect("wagtail_subscriptions_admin:customers")

    def _bulk_cancel_subscriptions(self, customer_ids):
        from ..payments import get_payment_processor
        from ..models.audit import AuditLog

        canceled_count = 0
        for customer_id in customer_ids:
            try:
                customer = Customer.objects.get(id=customer_id)
                active_subs = customer.user.subscriptions.filter(status__in=["active", "trialing"])

                for subscription in active_subs:
                    processor = get_payment_processor(subscription.payment_processor)
                    processor.cancel_subscription(subscription.external_id, at_period_end=True)

                    subscription.status = "canceled"
                    subscription.save()
                    canceled_count += 1

                    # Log the action
                    AuditLog.log_action(
                        user=self.request.user,
                        action="cancel",
                        model_name="Subscription",
                        object_id=subscription.id,
                        object_repr=str(subscription),
                        description=f"Bulk canceled subscription for {customer.user.email}",
                        request=self.request,
                    )
            except Exception as e:
                continue

        # Log bulk action
        AuditLog.log_action(
            user=self.request.user,
            action="bulk_action",
            model_name="Customer",
            description=f"Bulk canceled {canceled_count} subscriptions",
            request=self.request,
            extra_data={
                "customer_count": len(customer_ids),
                "canceled_count": canceled_count,
            },
        )

        messages.success(self.request, _(f"Canceled {canceled_count} subscriptions."))

    def _export_customers(self, customer_ids):
        import csv
        from django.http import HttpResponse
        from ..models.audit import AuditLog

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="customers.csv"'

        writer = csv.writer(response)
        writer.writerow(["Email", "Name", "Plan", "Status", "Created", "MRR"])

        customers = Customer.objects.filter(id__in=customer_ids).select_related("user")
        for customer in customers:
            subscription = customer.user.subscriptions.first()
            writer.writerow(
                [
                    customer.user.email,
                    customer.user.get_full_name() or customer.user.username,
                    subscription.plan.name if subscription else "None",
                    subscription.get_status_display() if subscription else "None",
                    customer.created_at.strftime("%Y-%m-%d"),
                    subscription.plan.price if subscription else 0,
                ]
            )

        # Log export action
        AuditLog.log_action(
            user=self.request.user,
            action="export",
            model_name="Customer",
            description=f"Exported {len(customer_ids)} customers to CSV",
            request=self.request,
            extra_data={"customer_count": len(customer_ids)},
        )

        return response


class SettingsView(AdminSubscriptionMixin, TemplateView):
    template_name = "wagtail_subscriptions/admin/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.conf import settings
        from ..forms import PaymentProcessorConfigForm

        context["payment_processors"] = getattr(settings, "WAGTAIL_SUBSCRIPTIONS", {}).get(
            "PAYMENT_PROCESSORS", {}
        )
        context["config_form"] = PaymentProcessorConfigForm()
        context["show_config_guide"] = True
        return context

    def post(self, request, *args, **kwargs):
        from ..forms import PaymentProcessorConfigForm

        form = PaymentProcessorConfigForm(request.POST)

        if form.is_valid():
            messages.success(
                request,
                _("Configuration guide updated. Please update your Django settings file."),
            )
        else:
            messages.error(request, _("Please correct the errors below."))

        return self.get(request, *args, **kwargs)
