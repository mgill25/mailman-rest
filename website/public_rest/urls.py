from django.conf.urls import patterns, url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'memberships', views.MembershipViewSet)
router.register(r'lists', views.MailingListViewSet)
router.register(r'domains', views.DomainViewSet)
router.register(r'emails', views.EmailViewSet)

# Wire up our API using automatic URL routing.
list_settings = views.MailingListViewSet.as_view({
    'get': 'settings',
})

# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
    url(r'^api/lists/(?P<pk>[0-9]+)/settings/$', list_settings, name='list-settings'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)
