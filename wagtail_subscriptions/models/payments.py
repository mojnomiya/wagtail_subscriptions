from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMethod(models.Model):
    """Store payment method information"""
    PAYMENT_TYPES = [
        ('card', _('Credit/Debit Card')),
        ('bank_account', _('Bank Account')),
        ('paypal', _('PayPal')),
        ('other', _('Other')),
    ]
    
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='card')
    
    # Card details (last 4 digits, brand, etc.)
    last_four = models.CharField(max_length=4, blank=True)
    brand = models.CharField(max_length=20, blank=True)
    exp_month = models.PositiveIntegerField(null=True, blank=True)
    exp_year = models.PositiveIntegerField(null=True, blank=True)
    
    # External payment processor data
    external_id = models.CharField(max_length=255, verbose_name=_('External ID'))
    payment_processor = models.CharField(max_length=50, default='stripe')
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')
    
    def __str__(self):
        if self.payment_type == 'card' and self.last_four:
            return f"{self.brand} ****{self.last_four}"
        return f"{self.get_payment_type_display()}"


class Invoice(models.Model):
    """Store invoice information"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('open', _('Open')),
        ('paid', _('Paid')),
        ('void', _('Void')),
        ('uncollectible', _('Uncollectible')),
    ]
    
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='invoices')
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='invoices')
    
    invoice_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Dates
    issue_date = models.DateTimeField()
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # External payment processor data
    external_id = models.CharField(max_length=255, blank=True, verbose_name=_('External ID'))
    payment_processor = models.CharField(max_length=50, default='stripe')
    
    # PDF storage
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer}"


class Payment(models.Model):
    """Store payment transaction information"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('succeeded', _('Succeeded')),
        ('failed', _('Failed')),
        ('canceled', _('Canceled')),
        ('refunded', _('Refunded')),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # External payment processor data
    external_id = models.CharField(max_length=255, verbose_name=_('External ID'))
    payment_processor = models.CharField(max_length=50, default='stripe')
    
    # Failure information
    failure_code = models.CharField(max_length=100, blank=True)
    failure_message = models.TextField(blank=True)
    
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.external_id} - ${self.amount} ({self.status})"


class WebhookEvent(models.Model):
    """Store webhook events from payment processors"""
    payment_processor = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    external_id = models.CharField(max_length=255, verbose_name=_('External Event ID'))
    
    data = models.JSONField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Webhook Event')
        verbose_name_plural = _('Webhook Events')
        unique_together = ['payment_processor', 'external_id']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment_processor} - {self.event_type} ({self.external_id})"