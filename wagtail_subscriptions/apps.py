from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSubscriptionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_subscriptions"
    verbose_name = _("Wagtail Subscriptions")
    
    def ready(self):
        # Import signal handlers
        from . import signals  # noqa