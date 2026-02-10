import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Dict

import requests

from .base import BasePaymentProcessor


class PaddlePaymentProcessor(BasePaymentProcessor):
    """Paddle payment processor implementation"""

    def setup(self):
        """Initialize Paddle with API credentials"""
        self.vendor_id = self.config.get("vendor_id")
        self.vendor_auth_code = self.config.get("vendor_auth_code")
        self.public_key = self.config.get("public_key")
        self.sandbox = self.config.get("sandbox", True)

        if not self.vendor_id or not self.vendor_auth_code:
            raise ValueError("Paddle vendor_id and vendor_auth_code are required")

        self.base_url = (
            "https://sandbox-vendors.paddle.com/api"
            if self.sandbox
            else "https://vendors.paddle.com/api"
        )

    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make authenticated Paddle API request"""
        data.update({"vendor_id": self.vendor_id, "vendor_auth_code": self.vendor_auth_code})

        try:
            response = requests.post(f"{self.base_url}/{endpoint}", data=data)
            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                raise ValueError(
                    f"Paddle API error: {result.get('error', {}).get('message', 'Unknown error')}"
                )

            return result.get("response", {})
        except requests.RequestException as e:
            raise ValueError(f"Paddle API request failed: {str(e)}")

    def create_customer(self, user, **kwargs) -> str:
        """Create Paddle customer"""
        data = {
            "email": user.email,
        }

        # Add optional customer data
        if user.get_full_name():
            data["name"] = user.get_full_name()

        try:
            result = self._make_request("2.0/user", data)
            return str(result.get("user_id"))
        except ValueError:
            # Customer might already exist, return user ID
            return f"paddle_customer_{user.id}"

    def create_subscription(self, customer_id: str, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Create a Paddle subscription"""
        data = {
            "plan_id": plan_id,
            "user_email": kwargs.get("email"),
            "user_country": kwargs.get("country", "US"),
            "user_postcode": kwargs.get("postcode", ""),
        }

        # Add trial period if specified
        if kwargs.get("trial_days"):
            data["trial_days"] = kwargs["trial_days"]

        result = self._make_request("2.0/subscription/users", data)

        return {
            "id": str(result.get("subscription_id")),
            "status": "active",
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            "trial_end": None,
            "checkout_url": result.get("checkout_url"),
        }

    def cancel_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel a Paddle subscription"""
        data = {"subscription_id": subscription_id}

        self._make_request("2.0/subscription/users_cancel", data)

        return {
            "id": subscription_id,
            "status": "canceled",
            "canceled_at": int(datetime.utcnow().timestamp()),
            "cancel_at_period_end": True,
        }

    def update_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """Update a Paddle subscription"""
        data = {"subscription_id": subscription_id}

        # Add updateable fields
        if "plan_id" in kwargs:
            data["plan_id"] = kwargs["plan_id"]
        if "quantity" in kwargs:
            data["quantity"] = kwargs["quantity"]
        if "prorate" in kwargs:
            data["prorate"] = kwargs["prorate"]

        result = self._make_request("2.0/subscription/users/update", data)

        return {
            "id": subscription_id,
            "status": "active",
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
        }

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve Paddle subscription details"""
        data = {"subscription_id": subscription_id}

        result = self._make_request("2.0/subscription/users", data)

        # Paddle returns a list, get first subscription
        subscription = result[0] if result else {}

        return {
            "id": str(subscription.get("subscription_id")),
            "status": subscription.get("state", "active").lower(),
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            "trial_end": None,
            "canceled_at": None,
        }

    def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process Paddle webhook"""
        import json
        from urllib.parse import parse_qs

        try:
            # Paddle sends form-encoded data
            if payload.startswith(b"{"):
                # JSON payload
                data = json.loads(payload.decode("utf-8"))
            else:
                # Form-encoded payload
                parsed = parse_qs(payload.decode("utf-8"))
                data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}

            # Verify webhook signature if public key is provided
            if self.public_key and signature:
                self._verify_webhook_signature(data, signature)

            return {
                "id": data.get("p_order_id") or data.get("subscription_id"),
                "type": data.get("alert_name"),
                "data": data,
                "created": int(datetime.utcnow().timestamp()),
            }
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid Paddle webhook payload: {str(e)}")

    def _verify_webhook_signature(self, data: Dict, signature: str) -> bool:
        """Verify Paddle webhook signature"""
        # Remove signature from data for verification
        data_copy = data.copy()
        data_copy.pop("p_signature", None)

        # Sort and serialize data
        sorted_data = sorted(data_copy.items())
        serialized = "&".join([f"{k}={v}" for k, v in sorted_data])

        # Verify signature
        expected_signature = hmac.new(
            self.public_key.encode("utf-8"), serialized.encode("utf-8"), hashlib.sha1
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid Paddle webhook signature")

        return True

    def charge_customer(
        self, customer_id: str, amount: float, currency: str = "USD", **kwargs
    ) -> Dict[str, Any]:
        """Charge a Paddle customer (one-time payment)"""
        data = {
            "title": kwargs.get("title", "One-time Payment"),
            "webhook_url": kwargs.get("webhook_url"),
            "prices": [f"{currency}:{amount}"],
        }

        if kwargs.get("customer_email"):
            data["customer_email"] = kwargs["customer_email"]

        result = self._make_request("2.0/product/generate_pay_link", data)

        return {
            "id": result.get("url", "").split("/")[-1],  # Extract ID from URL
            "status": "pending",
            "amount": amount,
            "currency": currency,
            "checkout_url": result.get("url"),
        }
