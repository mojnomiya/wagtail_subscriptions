from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone

from ..models import Customer, Invoice, Subscription


class InvoiceService:
    """Service for managing invoices"""

    @staticmethod
    def create_invoice_for_subscription(subscription: Subscription, **kwargs) -> Invoice:
        """Create an invoice for a subscription billing period"""

        # Calculate invoice amounts
        subtotal = subscription.plan.price
        tax_rate = kwargs.get("tax_rate", Decimal("0.00"))
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount

        # Generate invoice number
        invoice_number = InvoiceService._generate_invoice_number()

        # Set dates
        issue_date = kwargs.get("issue_date", timezone.now())
        due_date = kwargs.get("due_date", issue_date + timedelta(days=30))

        # Create invoice
        invoice = Invoice.objects.create(
            subscription=subscription,
            customer=subscription.user.customer_profile,
            invoice_number=invoice_number,
            status="open",
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=total,
            amount_due=total,
            issue_date=issue_date,
            due_date=due_date,
            payment_processor=subscription.payment_processor,
        )

        return invoice

    @staticmethod
    def _generate_invoice_number() -> str:
        """Generate unique invoice number"""
        # Get current date
        date_str = timezone.now().strftime("%Y%m")

        # Get next sequence number for this month
        last_invoice = (
            Invoice.objects.filter(invoice_number__startswith=f"INV-{date_str}")
            .order_by("-created_at")
            .first()
        )

        if last_invoice:
            # Extract sequence number and increment
            try:
                last_seq = int(last_invoice.invoice_number.split("-")[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        return f"INV-{date_str}-{next_seq:04d}"

    @staticmethod
    def mark_invoice_paid(invoice: Invoice, payment_amount: Decimal, payment_date: datetime = None):
        """Mark an invoice as paid"""
        if payment_date is None:
            payment_date = timezone.now()

        invoice.amount_paid += payment_amount
        invoice.amount_due = max(Decimal("0.00"), invoice.total - invoice.amount_paid)

        if invoice.amount_due == Decimal("0.00"):
            invoice.status = "paid"
            invoice.paid_at = payment_date

        invoice.save()

    @staticmethod
    def void_invoice(invoice: Invoice, reason: str = ""):
        """Void an invoice"""
        invoice.status = "void"
        invoice.save()
