from django.conf.urls import patterns, url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'memberships', views.MembershipViewSet)
router.register(r'lists', views.MailingListViewSet)
router.register(r'domains', views.DomainViewSet)
router.register(r'emails', views.EmailViewSet)

# Explicit routing, settings are secondary resources
listsettings_detail = views.ListSettingsViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
    url(r'^api/lists/(?P<pk>[0-9]+)/settings/$', listsettings_detail, name='listsettings-detail'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)
