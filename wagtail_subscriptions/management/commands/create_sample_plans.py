from django.core.management.base import BaseCommand
from wagtail_subscriptions.models import SubscriptionPlan, Module, Feature, PlanFeature


class Command(BaseCommand):
    help = 'Create sample subscription plans and features'

    def handle(self, *args, **options):
        # Create modules based on cashsheet structure
        accounting_module, _ = Module.objects.get_or_create(
            slug='accounting',
            defaults={
                'name': 'Accounting',
                'description': 'Core accounting and bookkeeping features',
                'icon': 'calculator',
                'is_active': True,
                'sort_order': 1
            }
        )
        
        reporting_module, _ = Module.objects.get_or_create(
            slug='reporting',
            defaults={
                'name': 'Reporting & Analytics',
                'description': 'Financial reports and business analytics',
                'icon': 'chart-bar',
                'is_active': True,
                'sort_order': 2
            }
        )
        
        collaboration_module, _ = Module.objects.get_or_create(
            slug='collaboration',
            defaults={
                'name': 'Team Collaboration',
                'description': 'Multi-user access and team features',
                'icon': 'users',
                'is_active': True,
                'sort_order': 3
            }
        )
        
        # Create features based on cashsheet functionality
        features_data = [
            # Accounting Module Features
            {
                'module': accounting_module,
                'name': 'Chart of Accounts',
                'slug': 'chart-of-accounts',
                'feature_type': 'binary',
                'description': 'Create and manage chart of accounts'
            },
            {
                'module': accounting_module,
                'name': 'Journal Entries',
                'slug': 'journal-entries',
                'feature_type': 'quota',
                'description': 'Monthly journal entries limit',
                'default_quota': 100,
                'quota_unit': 'entries/month'
            },
            {
                'module': accounting_module,
                'name': 'Bank Reconciliation',
                'slug': 'bank-reconciliation',
                'feature_type': 'binary',
                'description': 'Automated bank reconciliation'
            },
            {
                'module': accounting_module,
                'name': 'Invoicing',
                'slug': 'invoicing',
                'feature_type': 'quota',
                'description': 'Create and send invoices',
                'default_quota': 50,
                'quota_unit': 'invoices/month'
            },
            # Reporting Module Features
            {
                'module': reporting_module,
                'name': 'Financial Statements',
                'slug': 'financial-statements',
                'feature_type': 'binary',
                'description': 'Balance Sheet, Income Statement, Cash Flow'
            },
            {
                'module': reporting_module,
                'name': 'Custom Reports',
                'slug': 'custom-reports',
                'feature_type': 'quota',
                'description': 'Create custom financial reports',
                'default_quota': 5,
                'quota_unit': 'reports'
            },
            {
                'module': reporting_module,
                'name': 'Advanced Analytics',
                'slug': 'advanced-analytics',
                'feature_type': 'binary',
                'description': 'Business intelligence and forecasting'
            },
            # Collaboration Module Features
            {
                'module': collaboration_module,
                'name': 'Team Members',
                'slug': 'team-members',
                'feature_type': 'quota',
                'description': 'Number of team members',
                'default_quota': 1,
                'quota_unit': 'users'
            },
            {
                'module': collaboration_module,
                'name': 'Organizations',
                'slug': 'organizations',
                'feature_type': 'quota',
                'description': 'Number of organizations/entities',
                'default_quota': 1,
                'quota_unit': 'organizations'
            },
            {
                'module': collaboration_module,
                'name': 'Priority Support',
                'slug': 'priority-support',
                'feature_type': 'binary',
                'description': '24/7 priority customer support'
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
        
        # Create plans based on cashsheet pricing structure
        plans_data = [
            {
                'name': 'Starter',
                'slug': 'starter',
                'price': 0.00,
                'billing_period': 'monthly',
                'trial_period_days': 0,
                'description': 'Perfect for freelancers and small businesses getting started',
                'sort_order': 1
            },
            {
                'name': 'Professional',
                'slug': 'professional',
                'price': 29.00,
                'billing_period': 'monthly',
                'trial_period_days': 14,
                'description': 'For growing businesses with advanced accounting needs',
                'sort_order': 2
            },
            {
                'name': 'Premium',
                'slug': 'premium',
                'price': 79.00,
                'billing_period': 'monthly',
                'trial_period_days': 30,
                'description': 'For large organizations with unlimited access',
                'sort_order': 3
            }
        ]
        
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(f'Created plan: {plan.name}')
                
                # Associate features with plans based on cashsheet structure
                if plan.slug == 'starter':
                    # Starter plan - basic features with limits
                    starter_features = {
                        'chart-of-accounts': {'quota': None},
                        'journal-entries': {'quota': 50},
                        'invoicing': {'quota': 10},
                        'financial-statements': {'quota': None},
                        'team-members': {'quota': 1},
                        'organizations': {'quota': 1}
                    }
                    for feature_slug, config in starter_features.items():
                        PlanFeature.objects.get_or_create(
                            plan=plan, feature=features[feature_slug],
                            defaults={'is_included': True, 'quota_override': config['quota']}
                        )
                
                elif plan.slug == 'professional':
                    # Professional plan - expanded features
                    pro_features = {
                        'chart-of-accounts': {'quota': None},
                        'journal-entries': {'quota': 500},
                        'bank-reconciliation': {'quota': None},
                        'invoicing': {'quota': 100},
                        'financial-statements': {'quota': None},
                        'custom-reports': {'quota': 10},
                        'advanced-analytics': {'quota': None},
                        'team-members': {'quota': 5},
                        'organizations': {'quota': 3}
                    }
                    for feature_slug, config in pro_features.items():
                        PlanFeature.objects.get_or_create(
                            plan=plan, feature=features[feature_slug],
                            defaults={'is_included': True, 'quota_override': config['quota']}
                        )
                
                elif plan.slug == 'premium':
                    # Premium plan - unlimited access
                    premium_features = {
                        'chart-of-accounts': {'quota': None},
                        'journal-entries': {'quota': 9999},
                        'bank-reconciliation': {'quota': None},
                        'invoicing': {'quota': 9999},
                        'financial-statements': {'quota': None},
                        'custom-reports': {'quota': 9999},
                        'advanced-analytics': {'quota': None},
                        'team-members': {'quota': 9999},
                        'organizations': {'quota': 9999},
                        'priority-support': {'quota': None}
                    }
                    for feature_slug, config in premium_features.items():
                        PlanFeature.objects.get_or_create(
                            plan=plan, feature=features[feature_slug],
                            defaults={'is_included': True, 'quota_override': config['quota']}
                        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample plans and features')
        )