from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from wagtail_subscriptions.models import (
    Feature,
    Module,
    PlanFeature,
    Subscription,
    SubscriptionPlan,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Populate dummy subscription data for merchant to start"

    def handle(self, *args, **options):
        self.stdout.write("Creating subscription plans and features...")

        # Create modules
        core_module = Module.objects.get_or_create(
            slug="core-features", defaults={"name": "Core Features"}
        )[0]

        analytics_module = Module.objects.get_or_create(
            slug="analytics", defaults={"name": "Analytics & Reporting"}
        )[0]

        api_module = Module.objects.get_or_create(
            slug="api-access", defaults={"name": "API Access"}
        )[0]

        self.stdout.write(self.style.SUCCESS(f"✓ Created {Module.objects.count()} modules"))

        # Create features
        features_data = [
            {
                "module": core_module,
                "slug": "user-accounts",
                "name": "User Accounts",
                "feature_type": "quota",
                "default_quota": 5,
            },
            {
                "module": core_module,
                "slug": "storage",
                "name": "Storage (GB)",
                "feature_type": "quota",
                "default_quota": 10,
            },
            {
                "module": core_module,
                "slug": "projects",
                "name": "Projects",
                "feature_type": "quota",
                "default_quota": 3,
            },
            {
                "module": analytics_module,
                "slug": "basic-analytics",
                "name": "Basic Analytics",
                "feature_type": "boolean",
                "default_quota": None,
            },
            {
                "module": analytics_module,
                "slug": "advanced-analytics",
                "name": "Advanced Analytics",
                "feature_type": "boolean",
                "default_quota": None,
            },
            {
                "module": api_module,
                "slug": "api-access",
                "name": "API Access",
                "feature_type": "boolean",
                "default_quota": None,
            },
            {
                "module": api_module,
                "slug": "api-calls",
                "name": "API Calls per Month",
                "feature_type": "quota",
                "default_quota": 1000,
            },
        ]

        features = {}
        for feature_data in features_data:
            feature, created = Feature.objects.get_or_create(
                slug=feature_data["slug"],
                defaults={
                    "module": feature_data["module"],
                    "name": feature_data["name"],
                    "feature_type": feature_data["feature_type"],
                    "default_quota": feature_data["default_quota"],
                },
            )
            features[feature_data["slug"]] = feature

        self.stdout.write(self.style.SUCCESS(f"✓ Created {Feature.objects.count()} features"))

        # Create subscription plans
        plans_data = [
            {
                "name": "Free",
                "slug": "free",
                "price": Decimal("0.00"),
                "billing_period": "monthly",
                "trial_period_days": 0,
                "is_active": True,
                "description": "Perfect for getting started",
                "features": {
                    "user-accounts": 1,
                    "storage": 5,
                    "projects": 1,
                    "basic-analytics": True,
                },
            },
            {
                "name": "Starter",
                "slug": "starter",
                "price": Decimal("9.99"),
                "billing_period": "monthly",
                "trial_period_days": 14,
                "is_active": True,
                "description": "Great for small teams",
                "features": {
                    "user-accounts": 5,
                    "storage": 25,
                    "projects": 5,
                    "basic-analytics": True,
                    "api-access": True,
                    "api-calls": 5000,
                },
            },
            {
                "name": "Professional",
                "slug": "pro",
                "price": Decimal("29.99"),
                "billing_period": "monthly",
                "trial_period_days": 14,
                "is_active": True,
                "description": "For growing businesses",
                "features": {
                    "user-accounts": 25,
                    "storage": 100,
                    "projects": 25,
                    "basic-analytics": True,
                    "advanced-analytics": True,
                    "api-access": True,
                    "api-calls": 50000,
                },
            },
            {
                "name": "Enterprise",
                "slug": "enterprise",
                "price": Decimal("99.99"),
                "billing_period": "monthly",
                "trial_period_days": 30,
                "is_active": True,
                "description": "For large organizations",
                "features": {
                    "user-accounts": None,  # Unlimited
                    "storage": 1000,
                    "projects": None,  # Unlimited
                    "basic-analytics": True,
                    "advanced-analytics": True,
                    "api-access": True,
                    "api-calls": None,  # Unlimited
                },
            },
        ]

        for plan_data in plans_data:
            plan_features = plan_data.pop("features")
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data["slug"], defaults=plan_data
            )

            # Add features to plan
            for feature_slug, quota in plan_features.items():
                feature = features[feature_slug]
                PlanFeature.objects.get_or_create(
                    plan=plan,
                    feature=feature,
                    defaults={
                        "is_included": True,
                        "quota_override": quota,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {SubscriptionPlan.objects.count()} plans")
        )

        # Create demo user with subscription
        demo_user, created = User.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@example.com",
                "is_staff": False,
                "is_superuser": False,
            },
        )
        if created:
            demo_user.set_password("demo123")
            demo_user.save()

        # Create subscription for demo user
        pro_plan = SubscriptionPlan.objects.get(slug="pro")
        now = timezone.now()
        subscription, created = Subscription.objects.get_or_create(
            user=demo_user,
            defaults={
                "plan": pro_plan,
                "status": "active",
                "current_period_start": now,
                "current_period_end": now + timezone.timedelta(days=30),
            },
        )

        self.stdout.write(self.style.SUCCESS(f"✓ Created demo user with subscription"))

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✓ Dummy data created successfully!"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"\nModules: {Module.objects.count()}")
        self.stdout.write(f"Features: {Feature.objects.count()}")
        self.stdout.write(f"Plans: {SubscriptionPlan.objects.count()}")
        self.stdout.write(f"\nDemo User:")
        self.stdout.write(f"  Username: demo")
        self.stdout.write(f"  Password: demo123")
        self.stdout.write(f"  Plan: {subscription.plan.name}")
        self.stdout.write(f"\nYou can now:")
        self.stdout.write(f"  1. View pricing: http://localhost:8000/subscriptions/pricing/")
        self.stdout.write(f"  2. Login as demo user")
        self.stdout.write(f"  3. Access admin: http://localhost:8000/admin/")
        self.stdout.write("")
