from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class Module(models.Model):
    """Feature modules for organizing subscription features"""
    name = models.CharField(max_length=100, verbose_name=_('Module Name'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    icon = models.CharField(max_length=50, blank=True, help_text=_('CSS icon class'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Sort Order'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('slug'),
            FieldPanel('description'),
            FieldPanel('icon'),
        ], heading=_('Basic Information')),
        MultiFieldPanel([
            FieldPanel('is_active'),
            FieldPanel('sort_order'),
        ], heading=_('Settings')),
    ]
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = _('Module')
        verbose_name_plural = _('Modules')
    
    def __str__(self):
        return self.name


@register_snippet
class Feature(models.Model):
    """Individual features that can be included in subscription plans"""
    FEATURE_TYPES = [
        ('binary', _('Binary (On/Off)')),
        ('quota', _('Quota (Usage Limit)')),
        ('tiered', _('Tiered (Multiple Levels)')),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='features')
    name = models.CharField(max_length=100, verbose_name=_('Feature Name'))
    slug = models.SlugField(verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPES, default='binary')
    
    # For quota-based features
    default_quota = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Default Quota'))
    quota_unit = models.CharField(max_length=50, blank=True, verbose_name=_('Quota Unit'))
    
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Sort Order'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('module'),
            FieldPanel('name'),
            FieldPanel('slug'),
            FieldPanel('description'),
            FieldPanel('feature_type'),
        ], heading=_('Basic Information')),
        MultiFieldPanel([
            FieldPanel('default_quota'),
            FieldPanel('quota_unit'),
        ], heading=_('Quota Settings')),
        MultiFieldPanel([
            FieldPanel('is_active'),
            FieldPanel('sort_order'),
        ], heading=_('Settings')),
    ]
    
    class Meta:
        ordering = ['module', 'sort_order', 'name']
        verbose_name = _('Feature')
        verbose_name_plural = _('Features')
        unique_together = ['module', 'slug']
    
    def __str__(self):
        return f"{self.module.name} - {self.name}"


@register_snippet
class PlanFeature(models.Model):
    """Many-to-many relationship between plans and features with custom settings"""
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.CASCADE, related_name='plan_features')
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='plan_features')
    
    # Feature-specific settings
    is_included = models.BooleanField(default=True, verbose_name=_('Included'))
    quota_override = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Quota Override'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('plan'),
            FieldPanel('feature'),
        ], heading=_('Association')),
        MultiFieldPanel([
            FieldPanel('is_included'),
            FieldPanel('quota_override'),
        ], heading=_('Feature Settings')),
    ]
    
    class Meta:
        verbose_name = _('Plan Feature')
        verbose_name_plural = _('Plan Features')
        unique_together = ['plan', 'feature']
    
    def __str__(self):
        return f"{self.plan.name} - {self.feature.name}"
    
    @property
    def effective_quota(self):
        """Get the effective quota for this feature in this plan"""
        return self.quota_override or self.feature.default_quota


class UsageRecord(models.Model):
    """Track feature usage for quota-based features"""
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='usage_records')
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='usage_records')
    
    usage_count = models.PositiveIntegerField(default=0)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Usage Record')
        verbose_name_plural = _('Usage Records')
        unique_together = ['subscription', 'feature', 'period_start']
        indexes = [
            models.Index(fields=['subscription', 'feature']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.subscription} - {self.feature.name}: {self.usage_count}"