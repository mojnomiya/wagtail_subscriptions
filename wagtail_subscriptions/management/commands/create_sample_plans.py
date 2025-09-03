from django.core.management.base import BaseCommand
from wagtail_subscriptions.models import SubscriptionPlan, Module, Feature, PlanFeature


class Command(BaseCommand):
    help = 'Create sample subscription plans and features'

    def handle(self, *args, **options):
        # Create modules
        core_module, _ = Module.objects.get_or_create(
            slug='core-features',
            defaults={
                'name': 'Core Features',
                'description': 'Essential features for all users',
                'is_active': True,
                'sort_order': 1
            }
        )
        
        advanced_module, _ = Module.objects.get_or_create(
            slug='advanced-features',
            defaults={
                'name': 'Advanced Features',
                'description': 'Premium features for power users',
                'is_active': True,
                'sort_order': 2
            }
        )
        
        # Create features
        features_data = [
            {
                'module': core_module,
                'name': 'Basic Support',
                'slug': 'basic-support',
                'feature_type': 'binary',
                'description': 'Email support during business hours'
            },
            {
                'module': core_module,
                'name': 'API Access',
                'slug': 'api-access',
                'feature_type': 'quota',
                'description': 'REST API access',
                'default_quota': 1000,
                'quota_unit': 'requests/month'
            },
            {
                'module': advanced_module,
                'name': 'Priority Support',
                'slug': 'priority-support',
                'feature_type': 'binary',
                'description': '24/7 priority support'
            },
            {
                'module': advanced_module,
                'name': 'Advanced Analytics',
                'slug': 'advanced-analytics',
                'feature_type': 'binary',
                'description': 'Detailed analytics and reporting'
            },
            {
                'module': advanced_module,
                'name': 'Team Members',
                'slug': 'team-members',
                'feature_type': 'quota',
                'description': 'Number of team members',
                'default_quota': 5,
                'quota_unit': 'members'
            }
        ]
        
        features = {}
        for feature_data in features_data:
            feature, _ = Feature.objects.get_or_create(
                slug=feature_data['slug'],
                module=feature_data['module'],
                defaults=feature_data
            )
            features[feature_data['slug']] = feature
        
        # Create plans
        plans_data = [
            {
                'name': 'Free',
                'slug': 'free',
                'price': 0.00,
                'billing_period': 'monthly',
                'trial_period_days': 0,
                'description': 'Perfect for getting started'
            },
            {
                'name': 'Professional',
                'slug': 'professional',
                'price': 29.99,
                'billing_period': 'monthly',
                'trial_period_days': 14,
                'description': 'For growing businesses'
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'price': 99.99,
                'billing_period': 'monthly',
                'trial_period_days': 30,
                'description': 'For large organizations'
            }
        ]
        
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(f'Created plan: {plan.name}')
                
                # Associate features with plans
                if plan.slug == 'free':
                    PlanFeature.objects.get_or_create(
                        plan=plan, feature=features['basic-support'],
                        defaults={'is_included': True}
                    )
                    PlanFeature.objects.get_or_create(
                        plan=plan, feature=features['api-access'],
                        defaults={'is_included': True, 'quota_override': 100}
                    )
                
                elif plan.slug == 'professional':
                    for feature_slug in ['basic-support', 'api-access', 'advanced-analytics']:
                        quota_override = 5000 if feature_slug == 'api-access' else None
                        PlanFeature.objects.get_or_create(
                            plan=plan, feature=features[feature_slug],
                            defaults={'is_included': True, 'quota_override': quota_override}
                        )
                    PlanFeature.objects.get_or_create(
                        plan=plan, feature=features['team-members'],
                        defaults={'is_included': True, 'quota_override': 10}
                    )
                
                elif plan.slug == 'enterprise':
                    for feature_slug in features.keys():
                        quota_override = None
                        if feature_slug == 'api-access':
                            quota_override = 50000
                        elif feature_slug == 'team-members':
                            quota_override = 100
                        
                        PlanFeature.objects.get_or_create(
                            plan=plan, feature=features[feature_slug],
                            defaults={'is_included': True, 'quota_override': quota_override}
                        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample plans and features')
        )