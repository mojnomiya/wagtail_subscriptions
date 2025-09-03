from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext as _
from wagtail_subscriptions.models import Subscription


class Command(BaseCommand):
    help = 'Check for expired subscriptions and update their status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Find expired trials
        expired_trials = Subscription.objects.filter(
            status='trialing',
            trial_end__lt=now
        )
        
        # Find expired subscriptions
        expired_subscriptions = Subscription.objects.filter(
            status='active',
            current_period_end__lt=now
        )
        
        if dry_run:
            self.stdout.write(f"Would update {expired_trials.count()} expired trials")
            self.stdout.write(f"Would update {expired_subscriptions.count()} expired subscriptions")
        else:
            # Update expired trials
            updated_trials = expired_trials.update(status='past_due')
            self.stdout.write(f"Updated {updated_trials} expired trials")
            
            # Update expired subscriptions
            updated_subs = expired_subscriptions.update(status='past_due')
            self.stdout.write(f"Updated {updated_subs} expired subscriptions")
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully processed expired subscriptions")
            )