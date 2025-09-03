from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Customer, Subscription

User = get_user_model()


@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    """Create a customer profile when a user is created"""
    if created:
        Customer.objects.get_or_create(
            user=instance,
            defaults={
                'billing_email': instance.email,
            }
        )


@receiver(pre_save, sender=Subscription)
def update_subscription_status(sender, instance, **kwargs):
    """Update subscription status based on dates and external data"""
    # This would contain logic to sync with payment processor
    # and update status based on current date vs. trial_end, etc.
    pass