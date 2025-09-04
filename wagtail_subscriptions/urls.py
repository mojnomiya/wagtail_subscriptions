from django.urls import path, include
from . import views
from .views.api import PricingPlansAPIView

app_name = 'wagtail_subscriptions'

urlpatterns = [
    # Customer-facing URLs
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('subscribe/<slug:plan_slug>/', views.SubscribeView.as_view(), name='subscribe'),
    path('portal/', views.CustomerPortalView.as_view(), name='customer_portal'),
    
    # Admin URLs
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    
    # Webhook URLs
    path('webhooks/', include([
        path('stripe/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
    ])),
    
    # API URLs
    path('api/', include([
        path('subscription/', views.SubscriptionAPIView.as_view(), name='subscription_api'),
        path('analytics/', views.AnalyticsAPIView.as_view(), name='analytics_api'),
        path('plans/', PricingPlansAPIView.as_view(), name='api_plans'),
    ])),
]