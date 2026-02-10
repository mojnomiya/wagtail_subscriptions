import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory

from wagtail_subscriptions.models import Feature, Module, Subscription, SubscriptionPlan
from wagtail_subscriptions.permissions.decorators import (
    feature_required,
    subscription_required,
)

User = get_user_model()


@pytest.mark.django_db
class TestSubscriptionRequired:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser_sub", email="test_sub@example.com", password="testpass123"
        )

    def test_with_active_subscription(self, subscription):
        @subscription_required
        def test_view(request):
            return HttpResponse("success")

        request = self.factory.get("/")
        request.user = subscription.user

        response = test_view(request)
        assert response.status_code == 200
        assert hasattr(request, "subscription")

    def test_without_subscription(self):
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.sessions.middleware import SessionMiddleware
        
        @subscription_required
        def test_view(request):
            return HttpResponse("success")

        request = self.factory.get("/")
        request.user = self.user
        
        # Add session and messages middleware
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        setattr(request, '_messages', FallbackStorage(request))

        response = test_view(request)
        assert response.status_code == 302  # Redirect to pricing


@pytest.mark.django_db
class TestFeatureRequired:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser_feat", email="test_feat@example.com", password="testpass123"
        )

    def test_with_feature_access(self, subscription, feature):
        subscription.plan.plan_features.create(feature=feature, is_included=True)

        @feature_required("test-feature")
        def test_view(request):
            return HttpResponse("success")

        request = self.factory.get("/")
        request.user = subscription.user

        response = test_view(request)
        assert response.status_code == 200

    def test_without_feature_access(self, subscription):
        @feature_required("nonexistent-feature")
        def test_view(request):
            return HttpResponse("success")

        request = self.factory.get("/")
        request.user = subscription.user

        response = test_view(request)
        assert response.status_code == 302  # Redirect to pricing
