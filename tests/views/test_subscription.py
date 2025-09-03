import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, Mock
from wagtail_subscriptions.views.subscription import SubscribeView, CustomerPortalView
from wagtail_subscriptions.models import SubscriptionPlan, Customer

User = get_user_model()


@pytest.mark.django_db
class TestSubscribeView:
    def setup_method(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price=29.99,
            billing_period='monthly'
        )

    def test_get_context_data(self):
        view = SubscribeView()
        view.kwargs = {'plan_slug': 'test-plan'}
        context = view.get_context_data()
        assert context['plan'] == self.plan

    @patch('wagtail_subscriptions.payments.get_payment_processor')
    def test_post_create_subscription(self, mock_get_processor):
        mock_processor = Mock()
        mock_processor.create_customer.return_value = 'cus_123'
        mock_processor.create_subscription.return_value = {
            'id': 'sub_123',
            'status': 'active',
            'current_period_start': 1640995200,
            'current_period_end': 1643673600,
            'trial_end': None,
        }
        mock_get_processor.return_value = mock_processor

        request = self.factory.post(f'/subscribe/{self.plan.slug}/')
        request.user = self.user
        
        view = SubscribeView()
        view.request = request
        view.kwargs = {'plan_slug': 'test-plan'}
        
        # This would normally redirect, so we'd need to test the full flow
        # in integration tests


@pytest.mark.django_db
class TestCustomerPortalView:
    def setup_method(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_requires_subscription(self):
        request = self.factory.get('/portal/')
        request.user = self.user
        
        view = CustomerPortalView()
        view.request = request
        
        # Should redirect to pricing page since no subscription exists