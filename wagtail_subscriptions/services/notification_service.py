from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from ..models import Subscription


class NotificationService:
    """Service for sending notifications"""

    @staticmethod
    def send_payment_failed_notification(subscription):
        """Send notification for failed payment"""
        context = {
            "subscription": subscription,
            "customer": subscription.user,
            "plan": subscription.plan,
        }

        subject = f"Payment Failed - {subscription.plan.name}"
        html_message = render_to_string("wagtail_subscriptions/emails/payment_failed.html", context)
        text_message = render_to_string("wagtail_subscriptions/emails/payment_failed.txt", context)

        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[subscription.user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_subscription_canceled_notification(subscription):
        """Send notification for subscription cancellation"""
        context = {
            "subscription": subscription,
            "customer": subscription.user,
            "plan": subscription.plan,
        }

        subject = f"Subscription Canceled - {subscription.plan.name}"
        html_message = render_to_string(
            "wagtail_subscriptions/emails/subscription_canceled.html", context
        )
        text_message = render_to_string(
            "wagtail_subscriptions/emails/subscription_canceled.txt", context
        )

        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[subscription.user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_trial_ending_notification(subscription, days_remaining=3):
        """Send notification when trial is ending"""
        context = {
            "subscription": subscription,
            "customer": subscription.user,
            "plan": subscription.plan,
            "days_remaining": days_remaining,
        }

        subject = f"Your trial ends in {days_remaining} days"
        html_message = render_to_string("wagtail_subscriptions/emails/trial_ending.html", context)
        text_message = render_to_string("wagtail_subscriptions/emails/trial_ending.txt", context)

        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[subscription.user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_admin_notification(subject, message, notification_type="info"):
        """Send notification to admin users"""
        admin_emails = getattr(settings, "SUBSCRIPTION_ADMIN_EMAILS", [])
        if not admin_emails:
            return

        send_mail(
            subject=f"[Subscriptions] {subject}",
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=admin_emails,
            fail_silently=True,
        )

    @staticmethod
    def check_trial_endings():
        """Check for trials ending soon and send notifications"""
        from datetime import timedelta

        from django.utils import timezone

        # Find trials ending in 3 days
        three_days_from_now = timezone.now() + timedelta(days=3)
        ending_trials = Subscription.objects.filter(
            status="trialing", trial_end__date=three_days_from_now.date()
        )

        for subscription in ending_trials:
            NotificationService.send_trial_ending_notification(subscription, 3)

        return ending_trials.count()

    @staticmethod
    def check_failed_payments():
        """Check for failed payments and send notifications"""
        from ..models import Payment

        # Find recent failed payments
        yesterday = timezone.now() - timedelta(days=1)
        failed_payments = Payment.objects.filter(
            status="failed", created_at__gte=yesterday
        ).select_related("subscription")

        for payment in failed_payments:
            NotificationService.send_payment_failed_notification(payment.subscription)

        return failed_payments.count()
