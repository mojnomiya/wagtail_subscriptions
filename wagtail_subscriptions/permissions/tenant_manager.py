class TenantSubscriptionManager:
    """Handles subscription permissions for both single-tenant and multi-tenant modes"""
    
    @staticmethod
    def is_multi_tenant():
        """Auto-detect if running in multi-tenant mode"""
        try:
            import django_tenants
            return True
        except ImportError:
            return False
    
    @staticmethod
    def get_active_plan(request):
        """Get active subscription plan based on mode"""
        if hasattr(request, 'tenant') and request.tenant:
            # Multi-tenant mode: get plan from tenant
            return getattr(request.tenant, 'subscription_plan', None)
        else:
            # Single-tenant mode: get plan from user's subscription
            if hasattr(request, 'user') and request.user.is_authenticated:
                subscription = request.user.subscriptions.filter(
                    status__in=['active', 'trialing']
                ).first()
                return subscription.plan if subscription else None
        return None
    
    @staticmethod
    def has_feature_access(request, feature_slug):
        """Check if current context has access to feature"""
        plan = TenantSubscriptionManager.get_active_plan(request)
        if not plan:
            return False
        
        try:
            plan_feature = plan.plan_features.get(
                feature__slug=feature_slug,
                feature__is_active=True,
                is_included=True
            )
            return True
        except:
            return False
    
    @staticmethod
    def get_feature_quota(request, feature_slug):
        """Get quota for a specific feature"""
        plan = TenantSubscriptionManager.get_active_plan(request)
        if not plan:
            return 0
        
        try:
            plan_feature = plan.plan_features.get(
                feature__slug=feature_slug,
                feature__is_active=True,
                is_included=True
            )
            return plan_feature.effective_quota
        except:
            return 0
    
    @staticmethod
    def get_subscriber_info(request):
        """Get subscriber information for display"""
        if hasattr(request, 'tenant') and request.tenant:
            return {
                'type': 'tenant',
                'name': request.tenant.name,
                'schema': request.tenant.schema_name,
                'plan': request.tenant.subscription_plan.name if request.tenant.subscription_plan else 'No Plan'
            }
        elif hasattr(request, 'user') and request.user.is_authenticated:
            subscription = request.user.subscriptions.filter(status__in=['active', 'trialing']).first()
            return {
                'type': 'user',
                'name': request.user.get_full_name() or request.user.username,
                'plan': subscription.plan.name if subscription else 'No Plan'
            }
        return None