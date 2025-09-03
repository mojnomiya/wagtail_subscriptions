import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from wagtail_subscriptions.permissions.decorators import subscription_required, feature_required
from wagtail_subscriptions.models import SubscriptionPlan, Subscription, Module, Feature

User = get_user_model()


@pytest.mark.django_db
class TestSubscriptionRequired:
    def setup_method(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_with_active_subscription(self, subscription):
        @subscription_required
        def test_view(request):
            return HttpResponse('success')

        request = self.factory.get('/')
        request.user = subscription.user
        
        response = test_view(request)
        assert response.status_code == 200
        assert hasattr(request, 'subscription')

    def test_without_subscription(self):
        @subscription_required
        def test_view(request):
            return HttpResponse('success')

        request = self.factory.get('/')
        request.user = self.user
        
        response = test_view(request)
        assert response.status_code == 302  # Redirect to pricing


@pytest.mark.django_db
class TestFeatureRequired:
    def setup_method(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_with_feature_access(self, subscription, feature):
        subscription.plan.plan_features.create(feature=feature, is_included=True)
        
        @feature_required('test-feature')
        def test_view(request):
            return HttpResponse('success')

        request = self.factory.get('/')
        request.user = subscription.user
        
        response = test_view(request)
        assert response.status_code == 200

    def test_without_feature_access(self, subscription):
        @feature_required('nonexistent-feature')
        def test_view(request):
            return HttpResponse('success')

        request = self.factory.get('/')
        request.user = subscription.user
        
        response = test_view(request)
        assert response.status_code == 302  # Redirect to pricing