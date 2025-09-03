from django.contrib import admin
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.snippets.models import register_snippet
from .models import (
    SubscriptionPlan, Module, Feature, PlanFeature, 
    Subscription, Customer, UsageRecord
)
from .models.permissions import SubscriptionPermission, SubscriptionGroup


@register_snippet
class SubscriptionPlanAdmin(ModelAdmin):
    model = SubscriptionPlan
    menu_label = 'Subscription Plans'
    menu_icon = 'list-ul'
    list_display = ['name', 'price', 'billing_period', 'is_active', 'trial_period_days']
    list_filter = ['billing_period', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']


@register_snippet
class ModuleAdmin(ModelAdmin):
    model = Module
    menu_label = 'Modules'
    menu_icon = 'cogs'
    list_display = ['name', 'slug', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']


@register_snippet
class FeatureAdmin(ModelAdmin):
    model = Feature
    menu_label = 'Features'
    menu_icon = 'cog'
    list_display = ['name', 'module', 'feature_type', 'is_active']
    list_filter = ['module', 'feature_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['module', 'sort_order', 'name']


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ['plan', 'feature', 'is_included', 'quota_override']
    list_filter = ['is_included', 'plan', 'feature__module']
    search_fields = ['plan__name', 'feature__name']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_start', 'current_period_end']
    list_filter = ['status', 'plan', 'payment_processor']
    search_fields = ['user__username', 'user__email', 'plan__name']
    readonly_fields = ['external_id', 'created_at', 'updated_at']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'billing_email', 'created_at']
    search_fields = ['user__username', 'user__email', 'company_name', 'billing_email']
    readonly_fields = ['stripe_customer_id', 'created_at', 'updated_at']


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'feature', 'usage_count', 'period_start', 'period_end']
    list_filter = ['feature', 'subscription__plan']
    search_fields = ['subscription__user__username', 'feature__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SubscriptionPermission)
class SubscriptionPermissionAdmin(admin.ModelAdmin):
    list_display = ['feature', 'permission', 'created_at']
    list_filter = ['feature__module', 'permission__content_type']
    search_fields = ['feature__name', 'permission__name']


@admin.register(SubscriptionGroup)
class SubscriptionGroupAdmin(admin.ModelAdmin):
    list_display = ['plan', 'name', 'created_at']
    list_filter = ['plan']
    search_fields = ['plan__name', 'name']
    filter_horizontal = ['permissions']