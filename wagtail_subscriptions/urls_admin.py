from django.urls import path
from .views.admin import (
    SubscriptionDashboardView, PlansManagementView, 
    FeaturesManagementView, CustomersManagementView, SettingsView
)
from .views.plan_features import PlanFeatureManagementView

app_name = 'wagtail_subscriptions_admin'

urlpatterns = [
    path('', SubscriptionDashboardView.as_view(), name='dashboard'),
    path('plans/', PlansManagementView.as_view(), name='plans'),
    path('features/', FeaturesManagementView.as_view(), name='features'),
    path('plan-features/', PlanFeatureManagementView.as_view(), name='plan_features'),
    path('customers/', CustomersManagementView.as_view(), name='customers'),
    path('settings/', SettingsView.as_view(), name='settings'),
]