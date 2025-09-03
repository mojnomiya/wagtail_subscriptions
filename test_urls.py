from django.urls import path, include
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls

urlpatterns = [
    path('admin/', include(wagtailadmin_urls)),
    path('subscriptions/', include('wagtail_subscriptions.urls')),
    path('', include(wagtail_urls)),
]