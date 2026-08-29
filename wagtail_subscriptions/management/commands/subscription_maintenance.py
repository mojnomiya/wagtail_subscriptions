from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Subscription
from ...services.notification_service import NotificationService
from ...utils import reset_feature_usage_for_period


class Command(BaseCommand):
    help = "Run subscription maintenance tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--check-trials",
            action="store_true",
            help="Check for ending trials and send notifications",
        )
        parser.add_argument(
            "--check-payments",
            action="store_true",
            help="Check for failed payments and send notifications",
        )
        parser.add_argument(
            "--reset-usages",
            action="store_true",
            help="Reset feature usage records for all subscriptions",
        )
        parser.add_argument(
            "--cleanup-expired",
            action="store_true",
            help="Clean up expired trial subscriptions",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Run all maintenance tasks",
        )

    def handle(self, *args, **options):
        if options["all"]:
            options["check_trials"] = True
            options["check_payments"] = True
            options["reset_usages"] = True
            options["cleanup_expired"] = True

        if options["check_trials"]:
            self.check_trial_endings()

        if options["check_payments"]:
            self.check_failed_payments()

        if options["reset_usages"]:
            self.reset_all_usages()

        if options["cleanup_expired"]:
            self.cleanup_expired_trials()

    def check_trial_endings(self):
        """Check for trials ending soon"""
        self.stdout.write("Checking for ending trials...")

        count = NotificationService.check_trial_endings()

        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"Sent trial ending notifications to {count} customers")
            )
        else:
            self.stdout.write("No trials ending soon")

    def check_failed_payments(self):
        """Check for failed payments"""
        self.stdout.write("Checking for failed payments...")

        count = NotificationService.check_failed_payments()

        if count > 0:
            self.stdout.write(
                self.style.WARNING(f"Sent payment failure notifications for {count} payments")
            )
        else:
            self.stdout.write("No recent payment failures")

    def reset_all_usages(self):
        """Reset feature usage records for all subscriptions"""
        self.stdout.write("Resetting feature usage records...")

        from ...models import Subscription

        count = 0
        for subscription in Subscription.objects.filter(status__in=["active", "trialing"]):
            reset_feature_usage_for_period(subscription)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Reset usage records for {count} subscriptions"))

    def cleanup_expired_trials(self):
        """Clean up expired trial subscriptions"""
        self.stdout.write("Cleaning up expired trials...")

        now = timezone.now()
        expired_trials = Subscription.objects.filter(status="trialing", trial_end__lt=now)

        count = 0
        for subscription in expired_trials:
            # Cancel expired trials
            subscription.status = "canceled"
            subscription.canceled_at = now
            subscription.save()
            count += 1

            # Send notification
            NotificationService.send_subscription_canceled_notification(subscription)

        if count > 0:
            self.stdout.write(self.style.WARNING(f"Canceled {count} expired trial subscriptions"))
        else:
            self.stdout.write("No expired trials to clean up")
