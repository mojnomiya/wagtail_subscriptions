from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class SubscriptionPermission(models.Model):
    """Link Django permissions to subscription features"""
    feature = models.ForeignKey('Feature', on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Subscription Permission')
        verbose_name_plural = _('Subscription Permissions')
        unique_together = ['feature', 'permission']
    
    def __str__(self):
        return f"{self.feature.name} - {self.permission.name}"


class SubscriptionGroup(models.Model):
    """Groups for organizing subscription-based permissions"""
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100, verbose_name=_('Group Name'))
    permissions = models.ManyToManyField(Permission, blank=True, related_name='subscription_groups')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Subscription Group')
        verbose_name_plural = _('Subscription Groups')
        unique_together = ['plan', 'name']
    
    def __str__(self):
        return f"{self.plan.name} - {self.name}"