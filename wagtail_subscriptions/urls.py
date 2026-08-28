from django.urls import include, path

from . import views
from .views import plan_management, subscription, webhooks
from .views.api import (
    FeatureUsageAPIView,
    PricingPlansAPIView,
    SubscriptionAPIView,
    SubscriptionStatsAPIView,
    TrialStatsAPIView,
)

app_name = "wagtail_subscriptions"

urlpatterns = [
    # Customer-facing URLs
    path("pricing/", views.PricingView.as_view(), name="pricing"),
    path(
        "subscribe/<slug:plan_slug>/",
        subscription.SubscribeView.as_view(),
        name="subscribe",
    ),
    path(
        "success/",
        subscription.SubscriptionSuccessView.as_view(),
        name="subscription_success",
    ),
    path("portal/", subscription.CustomerPortalView.as_view(), name="customer_portal"),
    # Plan management
    path("change-plan/", plan_management.ChangePlanView.as_view(), name="change_plan"),
    path(
        "cancel/",
        plan_management.CancelSubscriptionView.as_view(),
        name="cancel_subscription",
    ),
    path(
        "reactivate/",
        plan_management.ReactivateSubscriptionView.as_view(),
        name="reactivate_subscription",
    ),
    # Webhook URLs
    path(
        "webhooks/",
        include(
            [
                path(
                    "stripe/",
                    webhooks.StripeWebhookView.as_view(),
                    name="stripe_webhook",
                ),
                path(
                    "paddle/",
                    webhooks.PaddleWebhookView.as_view(),
                    name="paddle_webhook",
                ),
                path(
                    "paypal/",
                    webhooks.PayPalWebhookView.as_view(),
                    name="paypal_webhook",
                ),
            ]
        ),
    ),
    # API URLs
    path(
        "api/",
        include(
            [
                path(
                    "subscription/",
                    SubscriptionAPIView.as_view(),
                    name="subscription_api",
                ),
                path("stats/", SubscriptionStatsAPIView.as_view(), name="subscription_stats"),
                path("trial-stats/", TrialStatsAPIView.as_view(), name="trial_stats"),
                path("plans/", PricingPlansAPIView.as_view(), name="api_plans"),
                path("feature-usage/", FeatureUsageAPIView.as_view(), name="feature_usage"),
            ]
        ),
    ),
]
