from django import forms
from django.utils.translation import gettext_lazy as _


class PaymentProcessorConfigForm(forms.Form):
    processor = forms.ChoiceField(
        choices=[
            ('stripe', 'Stripe'),
            ('paddle', 'Paddle'),
            ('paypal', 'PayPal'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Stripe fields
    stripe_public_key = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'pk_test_...'})
    )
    stripe_secret_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'sk_test_...'})
    )
    stripe_webhook_secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'whsec_...'})
    )
    
    # Paddle fields
    paddle_vendor_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345'})
    )
    paddle_vendor_auth_code = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    paddle_public_key = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    
    # PayPal fields
    paypal_client_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    paypal_client_secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    paypal_mode = forms.ChoiceField(
        choices=[('sandbox', 'Sandbox'), ('live', 'Live')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )