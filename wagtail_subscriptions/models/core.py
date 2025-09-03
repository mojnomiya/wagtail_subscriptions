from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet

User = get_user_model()


@register_snippet
class SubscriptionPlan(models.Model):
    BILLING_PERIODS = [
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('yearly', _('Yearly')),
        ('lifetime', _('Lifetime')),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_('Plan Name'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price'))
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIODS, default='monthly')
    trial_period_days = models.PositiveIntegerField(default=0, verbose_name=_('Trial Period (days)'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Sort Order'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('slug'),
            FieldPanel('description'),
        ], heading=_('Basic Information')),
        MultiFieldPanel([
            FieldPanel('price'),
            FieldPanel('billing_period'),
            FieldPanel('trial_period_days'),
        ], heading=_('Pricing')),
        MultiFieldPanel([
            FieldPanel('is_active'),
            FieldPanel('sort_order'),
        ], heading=_('Settings')),
    ]
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = _('Subscription Plan')
        verbose_name_plural = _('Subscription Plans')
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_period}"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('trialing', _('Trialing')),
        ('active', _('Active')),
        ('past_due', _('Past Due')),
        ('canceled', _('Canceled')),
        ('unpaid', _('Unpaid')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    
    # Billing information
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    trial_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # External payment processor data
    external_id = models.CharField(max_length=255, blank=True, verbose_name=_('External ID'))
    payment_processor = models.CharField(max_length=50, default='stripe')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['external_id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status in ['trialing', 'active']
    
    @property
    def is_trial(self):
        return self.status == 'trialing' and self.trial_end and timezone.now() < self.trial_end
    
    def has_feature_access(self, feature_slug):
        """Check if subscription has access to a specific feature"""
        try:
            plan_feature = self.plan.plan_features.get(
                feature__slug=feature_slug,
                feature__is_active=True,
                is_included=True
            )
            return True
        except:
            return False
    
    def get_feature_quota(self, feature_slug):
        """Get quota for a specific feature"""
        try:
            plan_feature = self.plan.plan_features.get(
                feature__slug=feature_slug,
                feature__is_active=True,
                is_included=True
            )
            return plan_feature.effective_quota
        except:
            return 0


class Customer(models.Model):
    """Extended customer information for billing"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    
    # Billing details
    company_name = models.CharField(max_length=255, blank=True)
    billing_email = models.EmailField(blank=True)
    tax_id = models.CharField(max_length=100, blank=True, verbose_name=_('Tax ID'))
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True)
    
    # External payment processor data
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"