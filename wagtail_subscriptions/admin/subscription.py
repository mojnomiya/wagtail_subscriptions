from django.contrib import admin
from django.utils.html import format_html
from ..models import Subscription, Customer, Invoice, Payment


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_end', 'is_active']
    list_filter = ['status', 'plan', 'created_at']
    search_fields = ['user__username', 'user__email', 'external_id']
    readonly_fields = ['external_id', 'created_at', 'updated_at']
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'billing_email', 'country']
    search_fields = ['user__username', 'user__email', 'company_name']
    readonly_fields = ['stripe_customer_id', 'created_at', 'updated_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'status', 'total', 'due_date']
    list_filter = ['status', 'created_at']
    search_fields = ['invoice_number', 'customer__user__email']
    readonly_fields = ['external_id', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['external_id', 'customer', 'amount', 'status', 'processed_at']
    list_filter = ['status', 'payment_processor', 'created_at']
    search_fields = ['external_id', 'customer__user__email']
    readonly_fields = ['external_id', 'created_at', 'updated_at']