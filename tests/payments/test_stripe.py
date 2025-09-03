import pytest
from unittest.mock import Mock, patch
from wagtail_subscriptions.payments.stripe import StripePaymentProcessor


class TestStripePaymentProcessor:
    def setup_method(self):
        self.config = {
            'secret_key': 'sk_test_123',
            'webhook_secret': 'whsec_123'
        }
        self.processor = StripePaymentProcessor(self.config)

    @patch('stripe.Customer.create')
    def test_create_customer(self, mock_create, user):
        mock_customer = Mock()
        mock_customer.id = 'cus_123'
        mock_create.return_value = mock_customer
        
        customer_id = self.processor.create_customer(user)
        assert customer_id == 'cus_123'
        mock_create.assert_called_once()

    @patch('stripe.Subscription.create')
    def test_create_subscription(self, mock_create):
        mock_subscription = Mock()
        mock_subscription.id = 'sub_123'
        mock_subscription.status = 'active'
        mock_subscription.current_period_start = 1640995200
        mock_subscription.current_period_end = 1643673600
        mock_subscription.trial_end = None
        mock_subscription.latest_invoice = None
        mock_create.return_value = mock_subscription
        
        result = self.processor.create_subscription('cus_123', 'price_123')
        assert result['id'] == 'sub_123'
        assert result['status'] == 'active'