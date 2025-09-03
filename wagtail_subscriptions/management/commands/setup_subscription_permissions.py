from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from wagtail_subscriptions.models import SubscriptionPlan, Module, Feature, Subscription, Customer


class Command(BaseCommand):
    help = 'Set up subscription management permissions'

    def handle(self, *args, **options):
        # Create subscription manager group
        subscription_managers, created = Group.objects.get_or_create(
            name='Subscription Managers'
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created "Subscription Managers" group')
            )
        
        # Get content types
        content_types = [
            ContentType.objects.get_for_model(SubscriptionPlan),
            ContentType.objects.get_for_model(Module),
            ContentType.objects.get_for_model(Feature),
            ContentType.objects.get_for_model(Subscription),
            ContentType.objects.get_for_model(Customer),
        ]
        
        # Add all permissions for subscription models
        permissions = []
        for ct in content_types:
            model_permissions = Permission.objects.filter(content_type=ct)
            permissions.extend(model_permissions)
            
        subscription_managers.permissions.set(permissions)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Added {len(permissions)} permissions to Subscription Managers group'
            )
        )
        
        # Create basic permissions for features
        self.stdout.write('Setting up feature permissions...')
        
        # Example: Create permissions for common features
        common_features = [
            'advanced_analytics',
            'api_access', 
            'priority_support',
            'custom_branding',
            'team_collaboration'
        ]
        
        for feature_slug in common_features:
            try:
                feature = Feature.objects.get(slug=feature_slug)
                # Create custom permission for this feature
                permission, created = Permission.objects.get_or_create(
                    codename=f'can_use_{feature_slug}',
                    name=f'Can use {feature.name}',
                    content_type=ContentType.objects.get_for_model(Feature)
                )
                if created:
                    self.stdout.write(f'Created permission: {permission.name}')
            except Feature.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Feature "{feature_slug}" not found')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up subscription permissions')
        )