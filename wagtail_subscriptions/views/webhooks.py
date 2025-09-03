import json
from django.http import HttpResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from ..models import Subscription, WebhookEvent
from ..payments import get_payment_processor


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """Handle Stripe webhook events"""
    
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            processor = get_payment_processor('stripe')
            event_data = processor.process_webhook(payload, sig_header)
            
            # Store webhook event
            webhook_event, created = WebhookEvent.objects.get_or_create(
                payment_processor='stripe',
                external_id=event_data['id'],
                defaults={
                    'event_type': event_data['type'],
                    'data': event_data['data'],
                }
            )
            
            if not created and webhook_event.processed:
                return HttpResponse(status=200)
            
            # Process the event
            self.process_event(event_data)
            
            # Mark as processed
            webhook_event.processed = True
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            
            return HttpResponse(status=200)
            
        except ValueError as e:
            return HttpResponse(status=400)
        except Exception as e:
            # Log error and mark webhook as failed
            if 'webhook_event' in locals():
                webhook_event.error_count += 1
                webhook_event.last_error = str(e)
                webhook_event.save()
            return HttpResponse(status=500)
    
    def process_event(self, event_data):
        """Process specific webhook events"""
        event_type = event_data['type']
        data = event_data['data']['object']
        
        if event_type == 'customer.subscription.updated':
            self.handle_subscription_updated(data)
        elif event_type == 'customer.subscription.deleted':
            self.handle_subscription_deleted(data)
        elif event_type == 'invoice.payment_succeeded':
            self.handle_payment_succeeded(data)
        elif event_type == 'invoice.payment_failed':
            self.handle_payment_failed(data)
    
    def handle_subscription_updated(self, subscription_data):
        """Handle subscription status updates"""
        try:
            subscription = Subscription.objects.get(external_id=subscription_data['id'])
            subscription.status = subscription_data['status']
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription_data['current_period_start'], tz=timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription_data['current_period_end'], tz=timezone.utc
            )
            if subscription_data.get('canceled_at'):
                subscription.canceled_at = timezone.datetime.fromtimestamp(
                    subscription_data['canceled_at'], tz=timezone.utc
                )
            subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    def handle_subscription_deleted(self, subscription_data):
        """Handle subscription cancellation"""
        try:
            subscription = Subscription.objects.get(external_id=subscription_data['id'])
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
            subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    def handle_payment_succeeded(self, invoice_data):
        """Handle successful payment"""
        # Update subscription status if needed
        pass
    
    def handle_payment_failed(self, invoice_data):
        """Handle failed payment"""
        # Update subscription status and notify customer
        pass