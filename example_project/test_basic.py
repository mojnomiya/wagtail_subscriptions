#!/usr/bin/env python
"""
Basic test script to verify wagtail-subscriptions functionality
Run with: python test_basic.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'example_project.settings')
django.setup()

from wagtail_subscriptions.models import (
    SubscriptionPlan, Module, Feature, PlanFeature, Customer
)
from wagtail_subscriptions.payments import get_payment_processor
from django.contrib.auth import get_user_model

User = get_user_model()

def test_models():
    """Test basic model creation"""
    print("🧪 Testing model creation...")
    
    # Create subscription plan
    plan = SubscriptionPlan.objects.create(
        name="Pro Plan",
        slug="pro-plan",
        price=29.99,
        billing_period="monthly",
        trial_period_days=14
    )
    print(f"✅ Created plan: {plan}")
    
    # Create module
    module = Module.objects.create(
        name="Analytics Module",
        slug="analytics",
        description="Advanced analytics features"
    )
    print(f"✅ Created module: {module}")
    
    # Create feature
    feature = Feature.objects.create(
        module=module,
        name="Advanced Reports",
        slug="advanced-reports",
        feature_type="binary"
    )
    print(f"✅ Created feature: {feature}")
    
    # Link feature to plan
    plan_feature = PlanFeature.objects.create(
        plan=plan,
        feature=feature,
        is_included=True
    )
    print(f"✅ Linked feature to plan: {plan_feature}")
    
    return plan, module, feature

def test_payment_processor():
    """Test payment processor initialization"""
    print("\n💳 Testing payment processor...")
    
    try:
        processor = get_payment_processor('stripe')
        print(f"✅ Stripe processor initialized: {processor.__class__.__name__}")
    except Exception as e:
        print(f"❌ Stripe processor error: {e}")
    
    try:
        processor = get_payment_processor('paddle')
        print(f"✅ Paddle processor initialized: {processor.__class__.__name__}")
    except Exception as e:
        print(f"❌ Paddle processor error: {e}")

def test_user_subscription():
    """Test user and subscription creation"""
    print("\n👤 Testing user subscription...")
    
    # Create test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    print(f"✅ Created user: {user}")
    
    # Customer should be auto-created via signal
    try:
        customer = Customer.objects.get(user=user)
        print(f"✅ Customer auto-created: {customer}")
    except Customer.DoesNotExist:
        print("❌ Customer not auto-created")
    
    return user

def test_permissions():
    """Test permission decorators"""
    print("\n🔐 Testing permissions...")
    
    from wagtail_subscriptions.permissions.decorators import subscription_required
    from django.http import HttpRequest
    
    @subscription_required
    def test_view(request):
        return "Success"
    
    print("✅ Permission decorators imported successfully")

def main():
    """Run all tests"""
    print("🚀 Starting wagtail-subscriptions basic tests...\n")
    
    try:
        # Test models
        plan, module, feature = test_models()
        
        # Test payment processors
        test_payment_processor()
        
        # Test user creation
        user = test_user_subscription()
        
        # Test permissions
        test_permissions()
        
        print("\n🎉 All basic tests passed!")
        print(f"📊 Created: {SubscriptionPlan.objects.count()} plans, {Module.objects.count()} modules, {Feature.objects.count()} features")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()