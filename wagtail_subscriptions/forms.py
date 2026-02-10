from django import forms


class PaymentProcessorConfigForm(forms.Form):
    processor = forms.ChoiceField(
        choices=[
            ("stripe", "Stripe"),
            ("paddle", "Paddle"),
            ("paypal", "PayPal"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    # Stripe fields
    stripe_public_key = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "pk_test_..."}),
    )
    stripe_secret_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "sk_test_..."}),
    )
    stripe_webhook_secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "whsec_..."}),
    )

    # Paddle fields
    paddle_vendor_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "12345"}),
    )
    paddle_vendor_auth_code = forms.CharField(
        required=False, widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    paddle_public_key = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
    )

    # PayPal fields
    paypal_client_id = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    paypal_client_secret = forms.CharField(
        required=False, widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    paypal_mode = forms.ChoiceField(
        choices=[("sandbox", "Sandbox"), ("live", "Live")],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        processor = cleaned_data.get("processor")

        if processor == "stripe":
            if not cleaned_data.get("stripe_secret_key"):
                raise forms.ValidationError("Stripe secret key is required for Stripe processor")
        elif processor == "paypal":
            if not cleaned_data.get("paypal_client_id") or not cleaned_data.get(
                "paypal_client_secret"
            ):
                raise forms.ValidationError(
                    "PayPal client ID and secret are required for PayPal processor"
                )
        elif processor == "paddle":
            if not cleaned_data.get("paddle_vendor_id") or not cleaned_data.get(
                "paddle_vendor_auth_code"
            ):
                raise forms.ValidationError(
                    "Paddle vendor ID and auth code are required for Paddle processor"
                )

        return cleaned_data
