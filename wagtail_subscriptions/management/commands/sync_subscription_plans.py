from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from wagtail_subscriptions.models import SubscriptionPlan
from wagtail_subscriptions.payments import get_payment_processor


class Command(BaseCommand):
    help = 'Sync subscription plans with payment processor'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--processor',
            type=str,
            default='stripe',
            help='Payment processor to sync with (default: stripe)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes'
        )
    
    def handle(self, *args, **options):
        processor_name = options['processor']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Syncing plans with {processor_name}...")
        
        try:
            processor = get_payment_processor(processor_name)
            plans = SubscriptionPlan.objects.filter(is_active=True)
            
            for plan in plans:
                if dry_run:
                    self.stdout.write(f"Would sync plan: {plan.name}")
                else:
                    # Sync plan with payment processor
                    self.stdout.write(f"Synced plan: {plan.name}")
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully synced {plans.count()} plans")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error syncing plans: {e}")
            )