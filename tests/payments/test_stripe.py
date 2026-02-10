from unittest.mock import Mock, patch

import pytest

from wagtail_subscriptions.payments.stripe import StripePaymentProcessor


class TestStripePaymentProcessor:
    def setup_method(self):
        self.config = {
            "secret_key": "sk_test_123",
            "public_key": "pk_test_123",
            "webhook_secret": "whsec_test_123",
        }
        self.processor = StripePaymentProcessor(self.config)

    @patch("stripe.Customer.create")
    def test_create_customer(self, mock_create, user):
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        mock_create.return_value = mock_customer

        customer_id = self.processor.create_customer(user)

        assert customer_id == "cus_test123"
        mock_create.assert_called_once()

    @patch("stripe.Subscription.create")
    def test_create_subscription(self, mock_create):
        mock_subscription = Mock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_subscription.current_period_start = 1640995200
        mock_subscription.current_period_end = 1643673600
        mock_subscription.trial_end = None
        mock_create.return_value = mock_subscription

        result = self.processor.create_subscription("cus_test123", "price_test123")

        assert result["id"] == "sub_test123"
        assert result["status"] == "active"
        mock_create.assert_called_once()

    @patch("stripe.Subscription.modify")
    def test_cancel_subscription(self, mock_modify):
        mock_subscription = Mock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "canceled"
        mock_subscription.canceled_at = 1640995200
        mock_subscription.cancel_at_period_end = True
        mock_modify.return_value = mock_subscription

        result = self.processor.cancel_subscription("sub_test123")

        assert result["status"] == "canceled"
        mock_modify.assert_called_once()

    @patch("stripe.error.StripeError")
    @patch("stripe.Subscription.modify")
    def test_cancel_subscription_error_handling(self, mock_modify, mock_error):
        mock_modify.side_effect = mock_error("Test error")

        with pytest.raises(ValueError, match="Stripe error"):
            self.processor.cancel_subscription("sub_test123")

    @patch("stripe.Webhook.construct_event")
    def test_process_webhook(self, mock_construct):
        mock_event = {
            "id": "evt_test123",
            "type": "invoice.payment_succeeded",
            "data": {"object": {"id": "in_test123"}},
            "created": 1640995200,
        }
        mock_construct.return_value = mock_event

        result = self.processor.process_webhook(b'{"test": "data"}', "test_signature")

        assert result["id"] == "evt_test123"
        assert result["type"] == "invoice.payment_succeeded"
        mock_construct.assert_called_once()
