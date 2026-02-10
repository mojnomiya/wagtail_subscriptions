from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AuditLog(models.Model):
    """Audit log for tracking admin actions"""

    ACTION_CHOICES = [
        ("create", _("Create")),
        ("update", _("Update")),
        ("delete", _("Delete")),
        ("cancel", _("Cancel")),
        ("reactivate", _("Reactivate")),
        ("export", _("Export")),
        ("bulk_action", _("Bulk Action")),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)

    # Details
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Metadata
    changes = models.JSONField(default=dict, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["model_name", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} at {self.created_at}"

    @classmethod
    def log_action(
        cls,
        user,
        action,
        model_name,
        object_id=None,
        object_repr=None,
        description=None,
        request=None,
        changes=None,
        extra_data=None,
    ):
        """Log an admin action"""

        # Get IP and user agent from request
        ip_address = None
        user_agent = ""
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        return cls.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id) if object_id else "",
            object_repr=object_repr or "",
            description=description or "",
            ip_address=ip_address,
            user_agent=user_agent,
            changes=changes or {},
            extra_data=extra_data or {},
        )

    @staticmethod
    def _get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
