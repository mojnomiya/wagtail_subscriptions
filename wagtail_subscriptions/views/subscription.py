from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ..models import Customer, Subscription, SubscriptionPlan
from ..payments import get_payment_processor
from ..permissions.mixins import SubscriptionRequiredMixin


class SubscribeView(LoginRequiredMixin, TemplateView):
    """Handle subscription creation"""

    template_name = "wagtail_subscriptions/subscription/subscribe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = get_object_or_404(SubscriptionPlan, slug=kwargs["plan_slug"], is_active=True)
        context["plan"] = plan
        return context

    def post(self, request, *args, **kwargs):
        plan = get_object_or_404(SubscriptionPlan, slug=kwargs["plan_slug"], is_active=True)

        # Check if user already has active subscription
        existing_sub = Subscription.objects.filter(
            user=request.user, status__in=["active", "trialing"]
        ).first()

        if existing_sub:
            messages.warning(request, _("You already have an active subscription."))
            return redirect("wagtail_subscriptions:customer_portal")

        # Get or create customer
        customer, created = Customer.objects.get_or_create(
            user=request.user, defaults={"billing_email": request.user.email}
        )

        try:
            # Create subscription via payment processor
            processor = get_payment_processor()

            # Create customer in payment processor if needed
            if not getattr(
                customer,
                f'{processor.__class__.__name__.lower().replace("paymentprocessor", "")}_customer_id',
                None,
            ):
                external_customer_id = processor.create_customer(
                    request.user,
                    email=request.user.email,
                    name=request.user.get_full_name() or request.user.username,
                )
                setattr(
                    customer,
                    f'{processor.__class__.__name__.lower().replace("paymentprocessor", "")}_customer_id',
                    external_customer_id,
                )
                customer.save()

            # Prepare subscription data
            subscription_kwargs = {
                "email": request.user.email,
                "trial_days": plan.trial_period_days if plan.trial_period_days > 0 else None,
            }

            subscription_data = processor.create_subscription(
                getattr(
                    customer,
                    f'{processor.__class__.__name__.lower().replace("paymentprocessor", "")}_customer_id',
                ),
                plan.slug,
                **subscription_kwargs,
            )

            # Create local subscription record
            from datetime import datetime

            from django.utils import timezone

            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                status=subscription_data["status"],
                external_id=subscription_data["id"],
                current_period_start=datetime.fromtimestamp(
                    subscription_data["current_period_start"], tz=timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    subscription_data["current_period_end"], tz=timezone.utc
                ),
                trial_end=(
                    datetime.fromtimestamp(subscription_data["trial_end"], tz=timezone.utc)
                    if subscription_data.get("trial_end")
                    else None
                ),
                payment_processor=processor.__class__.__name__.lower().replace(
                    "paymentprocessor", ""
                ),
            )

            # Handle approval URL for processors that need it (PayPal, Paddle)
            if "approval_url" in subscription_data or "checkout_url" in subscription_data:
                approval_url = subscription_data.get("approval_url") or subscription_data.get(
                    "checkout_url"
                )
                request.session["pending_subscription_id"] = subscription.id
                return redirect(approval_url)

            messages.success(request, _("Successfully subscribed to {}!").format(plan.name))
            return redirect("wagtail_subscriptions:subscription_success")

        except Exception as e:
            messages.error(request, _("Failed to create subscription: {}").format(str(e)))
            return self.get(request, *args, **kwargs)


class SubscriptionSuccessView(LoginRequiredMixin, TemplateView):
    """Subscription creation success page"""

    template_name = "wagtail_subscriptions/subscription/success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get most recent subscription for user
        subscription = (
            Subscription.objects.filter(user=self.request.user).order_by("-created_at").first()
        )
        context["subscription"] = subscription
        return context


class CustomerPortalView(SubscriptionRequiredMixin, TemplateView):
    """Customer self-service portal"""

    template_name = "wagtail_subscriptions/subscription/portal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subscription"] = self.subscription
        context["available_plans"] = SubscriptionPlan.objects.filter(is_active=True).exclude(
            id=self.subscription.plan_id
        )

        # Get billing history
        from ..models import Payment

        context["recent_payments"] = Payment.objects.filter(
            subscription=self.subscription
        ).order_by("-created_at")[:5]

        return context
