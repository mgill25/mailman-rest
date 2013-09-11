from django.conf.urls import patterns, url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
#router.register(r'memberships', views.MembershipViewSet)
router.register(r'domains', views.DomainViewSet)
router.register(r'lists', views.MailingListViewSet)
router.register(r'emails', views.EmailViewSet)

listsettings_detail = views.ListSettingsViewSet.as_view({
    'get': 'retrieve',
    'post': 'create',
    'put': 'update',
    'patch': 'partial_update',
})

emailprefs_detail = views.EmailPrefsViewSet.as_view({
    'get': 'retrieve',
    'post': 'create',
    'put': 'update',
    'patch': 'partial_update',
})

membership_detail = views.MembershipViewSet.as_view({
    'get': 'retrieve',
    'post': 'create',
    'put': 'update',
    'patch': 'partial_update',
})

membershipprefs_detail = views.MembershipPrefsViewSet.as_view({
    'get': 'retrieve',
    'post': 'create',
    'put': 'update',
    'patch': 'partial_update',
})

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^api/lists/(?P<pk>[^/]+)/settings/$', listsettings_detail, name='listsettings-detail'),
    url(r'^api/lists/(?P<pk>[^/]+)/settings/\.(?P<format>[a-z]+)$', listsettings_detail),
    url(r'^api/lists/(?P<list_id>[^/]+)/(?P<role>members|owners|moderators)/(?P<address>[^/]+)/$',
        membership_detail, name='membership-detail'),
    url(r'^api/', include(router.urls)),
    url(r'^api/emails/(?P<pk>[^/]+)/preferences/$', emailprefs_detail, name='emailprefs-detail'),
    url(r'^api/lists/(?P<list_id>[^/]+)/(?P<role>members|owners|moderators)/(?P<address>[^/]+)/preferences/$',
        membershipprefs_detail, name='membershipprefs-detail'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)
