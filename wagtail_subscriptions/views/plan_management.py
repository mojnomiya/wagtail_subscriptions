from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from ..models import Subscription, SubscriptionPlan
from ..payments import get_payment_processor
from ..permissions.mixins import SubscriptionRequiredMixin
from ..utils import calculate_proration


class ChangePlanView(SubscriptionRequiredMixin, View):
    """Handle subscription plan changes"""

    def post(self, request, *args, **kwargs):
        new_plan_slug = request.POST.get("plan_slug")
        if not new_plan_slug:
            messages.error(request, _("Plan selection is required."))
            return redirect("wagtail_subscriptions:customer_portal")

        new_plan = get_object_or_404(SubscriptionPlan, slug=new_plan_slug, is_active=True)
        current_subscription = self.subscription

        if new_plan.id == current_subscription.plan_id:
            messages.warning(request, _("You are already subscribed to this plan."))
            return redirect("wagtail_subscriptions:customer_portal")

        try:
            processor = get_payment_processor(current_subscription.payment_processor)

            # Calculate proration
            from django.utils import timezone

            days_remaining = (current_subscription.current_period_end - timezone.now()).days
            proration_amount = calculate_proration(
                current_subscription.plan, new_plan, days_remaining
            )

            # Update subscription in payment processor
            update_data = {
                "plan_id": new_plan.slug,
                "prorate": True if proration_amount != 0 else False,
            }

            processor_result = processor.update_subscription(
                current_subscription.external_id, **update_data
            )

            # Update local subscription
            current_subscription.plan = new_plan
            current_subscription.status = processor_result.get(
                "status", current_subscription.status
            )
            current_subscription.save()

            # Create usage records for new plan features
            self._setup_plan_features(current_subscription, new_plan)

            if proration_amount > 0:
                messages.success(
                    request,
                    _(
                        "Plan upgraded successfully! You will be charged ${:.2f} for the upgrade."
                    ).format(proration_amount),
                )
            elif proration_amount < 0:
                messages.success(
                    request,
                    _("Plan downgraded successfully! You will receive a credit of ${:.2f}.").format(
                        abs(proration_amount)
                    ),
                )
            else:
                messages.success(request, _("Plan changed successfully!"))

            return redirect("wagtail_subscriptions:customer_portal")

        except Exception as e:
            messages.error(request, _("Failed to change plan: {}").format(str(e)))
            return redirect("wagtail_subscriptions:customer_portal")

    def _setup_plan_features(self, subscription, new_plan):
        """Setup usage records for new plan features"""
        from ..models import UsageRecord

        # Reset usage records for the new billing period
        current_period_start = subscription.current_period_start

        for plan_feature in new_plan.plan_features.filter(is_included=True):
            if plan_feature.feature.feature_type == "quota":
                UsageRecord.objects.get_or_create(
                    subscription=subscription,
                    feature=plan_feature.feature,
                    period_start=current_period_start,
                    defaults={
                        "period_end": subscription.current_period_end,
                        "usage_count": 0,
                    },
                )


class CancelSubscriptionView(SubscriptionRequiredMixin, View):
    """Handle subscription cancellation"""

    def post(self, request, *args, **kwargs):
        cancel_immediately = request.POST.get("cancel_immediately") == "true"
        cancellation_reason = request.POST.get("reason", "")

        try:
            processor = get_payment_processor(self.subscription.payment_processor)

            # Cancel in payment processor
            cancel_data = {
                "at_period_end": not cancel_immediately,
                "reason": cancellation_reason,
            }

            processor_result = processor.cancel_subscription(
                self.subscription.external_id, **cancel_data
            )

            # Update local subscription
            from datetime import datetime

            from django.utils import timezone

            self.subscription.status = "canceled"
            if cancel_immediately:
                self.subscription.canceled_at = timezone.now()
            else:
                # Cancel at period end
                self.subscription.canceled_at = datetime.fromtimestamp(
                    processor_result.get("canceled_at", timezone.now().timestamp()),
                    tz=timezone.utc,
                )

            self.subscription.save()

            if cancel_immediately:
                messages.success(request, _("Subscription canceled immediately."))
            else:
                messages.success(
                    request,
                    _("Subscription will be canceled at the end of the current billing period."),
                )

            return redirect("wagtail_subscriptions:customer_portal")

        except Exception as e:
            messages.error(request, _("Failed to cancel subscription: {}").format(str(e)))
            return redirect("wagtail_subscriptions:customer_portal")


class ReactivateSubscriptionView(SubscriptionRequiredMixin, View):
    """Handle subscription reactivation"""

    def post(self, request, *args, **kwargs):
        if self.subscription.status != "canceled":
            messages.warning(request, _("Subscription is not canceled."))
            return redirect("wagtail_subscriptions:customer_portal")

        try:
            # For most processors, we need to create a new subscription
            processor = get_payment_processor(self.subscription.payment_processor)

            # Get customer ID
            customer = self.subscription.user.customer_profile
            processor_name = self.subscription.payment_processor
            customer_id_field = f"{processor_name}_customer_id"
            customer_id = getattr(customer, customer_id_field, None)

            if not customer_id:
                raise ValueError("Customer not found in payment processor")

            # Create new subscription
            subscription_data = processor.create_subscription(
                customer_id,
                self.subscription.plan.slug,
                email=self.subscription.user.email,
            )

            # Update local subscription
            from datetime import datetime

            from django.utils import timezone

            self.subscription.status = subscription_data["status"]
            self.subscription.external_id = subscription_data["id"]
            self.subscription.current_period_start = datetime.fromtimestamp(
                subscription_data["current_period_start"], tz=timezone.utc
            )
            self.subscription.current_period_end = datetime.fromtimestamp(
                subscription_data["current_period_end"], tz=timezone.utc
            )
            self.subscription.canceled_at = None
            self.subscription.save()

            messages.success(request, _("Subscription reactivated successfully!"))
            return redirect("wagtail_subscriptions:customer_portal")

        except Exception as e:
            messages.error(request, _("Failed to reactivate subscription: {}").format(str(e)))
            return redirect("wagtail_subscriptions:customer_portal")
