from django.urls import reverse, include, path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem
from wagtail.admin.site_summary import SummaryItem


@hooks.register('register_admin_urls')
def register_subscription_admin_urls():
    return [
        path('subscriptions/', include('wagtail_subscriptions.urls_admin', namespace='wagtail_subscriptions_admin')),
    ]


@hooks.register('register_admin_menu_item')
def register_subscriptions_menu_item():
    submenu = Menu(items=[
        MenuItem(_('Dashboard'), reverse('wagtail_subscriptions_admin:dashboard'), icon_name='home'),
        MenuItem(_('Plans'), '/admin/snippets/wagtail_subscriptions/subscriptionplan/', icon_name='list-ul'),
        MenuItem(_('Modules'), '/admin/snippets/wagtail_subscriptions/module/', icon_name='folder-open-inverse'),
        MenuItem(_('Features'), '/admin/snippets/wagtail_subscriptions/feature/', icon_name='cogs'),
        MenuItem(_('Plan Features'), reverse('wagtail_subscriptions_admin:plan_features'), icon_name='link'),
        MenuItem(_('Customers'), reverse('wagtail_subscriptions_admin:customers'), icon_name='group'),
        MenuItem(_('Settings'), reverse('wagtail_subscriptions_admin:settings'), icon_name='cog'),
    ])
    
    return SubmenuMenuItem(
        _('Subscriptions'),
        submenu,
        icon_name='user',
        order=300
    )


# Dashboard summary items removed due to SummaryItem compatibility issues