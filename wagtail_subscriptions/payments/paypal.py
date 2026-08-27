from datetime import datetime, timedelta
from typing import Any, Dict

import requests

from .base import BasePaymentProcessor


class PayPalPaymentProcessor(BasePaymentProcessor):
    """PayPal payment processor implementation"""

    def setup(self):
        """Initialize PayPal with API credentials"""
        self.client_id = self.config.get("client_id")
        self.client_secret = self.config.get("client_secret")
        self.mode = self.config.get("mode", "sandbox")
        self.validate_config(["client_id", "client_secret"])

        self.base_url = (
            "https://api.sandbox.paypal.com" if self.mode == "sandbox" else "https://api.paypal.com"
        )
        self.access_token = self._get_access_token()

        self.base_url = (
            "https://api.sandbox.paypal.com" if self.mode == "sandbox" else "https://api.paypal.com"
        )
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        """Get PayPal access token"""
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = "grant_type=client_credentials"

        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            return response.json()["access_token"]
        except requests.RequestException as e:
            raise ValueError(f"PayPal authentication failed: {str(e)}")

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated PayPal API request"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            response = requests.request(method, url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ValueError(f"PayPal API error: {str(e)}")

    def create_customer(self, user, **kwargs) -> str:
        """Create PayPal customer (not directly supported, return user reference)"""
        return f"paypal_customer_{user.id}"

    def create_subscription(self, customer_id: str, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Create a PayPal subscription"""
        start_time = (datetime.utcnow() + timedelta(minutes=1)).isoformat() + "Z"

        data = {
            "plan_id": plan_id,
            "start_time": start_time,
            "subscriber": {
                "name": {
                    "given_name": kwargs.get("first_name", "Customer"),
                    "surname": kwargs.get("last_name", "User"),
                },
                "email_address": kwargs.get("email", "customer@example.com"),
            },
            "application_context": {
                "brand_name": kwargs.get("brand_name", "Your Company"),
                "user_action": "SUBSCRIBE_NOW",
                "return_url": kwargs.get("return_url", "https://example.com/success"),
                "cancel_url": kwargs.get("cancel_url", "https://example.com/cancel"),
            },
        }

        result = self._make_request("POST", "/v1/billing/subscriptions", data)

        return {
            "id": result["id"],
            "status": result["status"].lower(),
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            "trial_end": None,
            "approval_url": next(
                (link["href"] for link in result.get("links", []) if link["rel"] == "approve"),
                None,
            ),
        }

    def cancel_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel a PayPal subscription"""
        data = {"reason": kwargs.get("reason", "User requested cancellation")}

        self._make_request("POST", f"/v1/billing/subscriptions/{subscription_id}/cancel", data)

        return {
            "id": subscription_id,
            "status": "canceled",
            "canceled_at": int(datetime.utcnow().timestamp()),
            "cancel_at_period_end": False,
        }

    def update_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Update a PayPal subscription (limited operations)"""
        # PayPal has limited update capabilities
        result = self.get_subscription(subscription_id)
        return result

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve PayPal subscription details"""
        result = self._make_request("GET", f"/v1/billing/subscriptions/{subscription_id}")

        return {
            "id": result["id"],
            "status": result["status"].lower(),
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            "trial_end": None,
            "canceled_at": None,
        }

    def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process PayPal webhook"""
        import json

        try:
            data = json.loads(payload.decode("utf-8"))
            return {
                "id": data.get("id"),
                "type": data.get("event_type"),
                "data": data.get("resource", {}),
                "created": int(datetime.utcnow().timestamp()),
            }
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid PayPal webhook payload: {str(e)}")

    def charge_customer(
        self, customer_id: str, amount: float, currency: str = "USD", **kwargs
    ) -> Dict[str, Any]:
        """Charge a PayPal customer (one-time payment)"""
        data = {
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": currency, "value": str(amount)}}],
        }

        result = self._make_request("POST", "/v2/checkout/orders", data)

        return {
            "id": result["id"],
            "status": result["status"].lower(),
            "amount": amount,
            "currency": currency,
            "approval_url": next(
                (link["href"] for link in result.get("links", []) if link["rel"] == "approve"),
                None,
            ),
        }
