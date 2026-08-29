from django.apps import apps
from django.core.management.base import BaseCommand

from wagtail_subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Sync tenant subscription plans (for multi-tenant setups)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-model",
            type=str,
            help="Tenant model path (e.g., myapp.Client). If not provided, will auto-detect.",
        )
        parser.add_argument(
            "--default-plan",
            type=str,
            help="Default plan slug to assign to tenants without plans. If not provided, uses first active plan.",
        )
        parser.add_argument(
            "--match-by",
            type=str,
            choices=["plan_type", "domain"],
            default="plan_type",
            help="Field to match tenants to plans by (default: plan_type)",
        )

    def handle(self, *args, **options):
        try:
            # Try to import django_tenants
            import django_tenants  # noqa: F401
        except ImportError:
            self.stdout.write(
                self.style.WARNING("django_tenants not installed. Skipping tenant sync.")
            )
            return

        tenant_model_path = options.get("tenant_model")

        if tenant_model_path:
            # Use specified tenant model
            try:
                app_label, model_name = tenant_model_path.split(".")
                TenantModel = apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                self.stdout.write(
                    self.style.ERROR(f"Could not find tenant model: {tenant_model_path}")
                )
                return
        else:
            # Auto-detect tenant model
            TenantModel = self._find_tenant_model()
            if not TenantModel:
                self.stdout.write(
                    self.style.ERROR(
                        "Could not auto-detect tenant model. Please specify with --tenant-model"
                    )
                )
                return

        # Get all tenants without subscription plans
        tenants_without_plans = TenantModel.objects.filter(subscription_plan__isnull=True)

        if not tenants_without_plans.exists():
            self.stdout.write(
                self.style.SUCCESS("All tenants already have subscription plans assigned.")
            )
            return

        # Get default plan
        default_plan_slug = options.get("default_plan")
        if default_plan_slug:
            try:
                default_plan = SubscriptionPlan.objects.get(slug=default_plan_slug, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Default plan '{default_plan_slug}' not found or not active.")
                )
                return
        else:
            default_plan = SubscriptionPlan.objects.filter(is_active=True).first()
            if not default_plan:
                self.stdout.write(
                    self.style.ERROR("No active subscription plans found. Create plans first.")
                )
                return

        # Assign default plan to tenants without plans
        updated_count = 0
        for tenant in tenants_without_plans:
            # Try to match by specified field
            match_field = options.get("match_by")
            matched = False

            if match_field == "plan_type" and hasattr(tenant, "plan_type") and tenant.plan_type:
                try:
                    plan = SubscriptionPlan.objects.get(slug=tenant.plan_type)
                    tenant.subscription_plan = plan
                    tenant.save()
                    updated_count += 1
                    self.stdout.write(
                        f"Assigned {plan.name} to {tenant.name} (matched by plan_type)"
                    )
                    matched = True
                except SubscriptionPlan.DoesNotExist:
                    pass

            if not matched:
                tenant.subscription_plan = default_plan
                tenant.save()
                updated_count += 1
                self.stdout.write(f"Assigned {default_plan.name} to {tenant.name} (default plan)")

        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} tenants."))

    def _find_tenant_model(self):
        """Auto-detect tenant model by looking for TenantMixin"""
        try:
            from django_tenants.models import TenantMixin

            for model in apps.get_models():
                if issubclass(model, TenantMixin) and hasattr(model, "subscription_plan"):
                    self.stdout.write(f"Auto-detected tenant model: {model._meta.label}")
                    return model
        except ImportError:
            pass
        return None
