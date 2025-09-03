from django.contrib import admin
from ..models import Module, Feature, PlanFeature, UsageRecord


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'module', 'feature_type', 'is_active', 'sort_order']
    list_filter = ['module', 'feature_type', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ['plan', 'feature', 'is_included', 'quota_override']
    list_filter = ['is_included', 'plan', 'feature__module']
    search_fields = ['plan__name', 'feature__name']


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'feature', 'usage_count', 'period_start', 'period_end']
    list_filter = ['feature', 'period_start']
    search_fields = ['subscription__user__email', 'feature__name']
    readonly_fields = ['created_at', 'updated_at']