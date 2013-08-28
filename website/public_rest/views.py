import logging

from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser

from public_rest.serializers import *
from public_rest.models import *
from public_rest.permissions import *

#logging
logger = logging.getLogger(__name__)


class BaseModelViewSet(viewsets.ModelViewSet):
    def str2bool(self, s):
        return s.lower() in ['true']


class UserViewSet(BaseModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = self.queryset
        display_name = self.request.QUERY_PARAMS.get('display_name', None)
        email = self.request.QUERY_PARAMS.get('email', None)
        # now filter out query params
        if display_name is not None:
            queryset = queryset.filter(display_name=display_name)
        if email is not None:
            queryset = queryset.filter(email__address=email)
        return queryset


class EmailViewSet(BaseModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    filter_fields = ('user', 'address', 'verified',)
    permission_classes = [IsValidOwnerPermission,
                          IsValidModeratorPermission,
                          IsAdminUser]

    def get_queryset(self):
        queryset = self.queryset
        address = self.request.QUERY_PARAMS.get('address', None)
        user = self.request.QUERY_PARAMS.get('user', None)
        verified = self.request.QUERY_PARAMS.get('verified', None)
        if address is not None:
            queryset = queryset.filter(address=address)
        if verified is not None:
            verified = self.str2bool(verified)
            queryset = queryset.filter(verified=verified)
        if user is not None:
            queryset = queryset.filter(user__display_name=user)
        return queryset


class MembershipViewSet(BaseModelViewSet):

    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminUser,]
    filter_fields = ('role', 'user',)

    def create(self, request):
        """Membership creation"""
        role = request.POST['role']
        list_name = request.POST['mlist']
        address = request.POST['address']

        try:
            mlist = MailingList.objects.get(fqdn_listname=list_name)
            logger.debug("List found! {0}".format(mlist))
        except MailingList.DoesNotExist:
            return response.Response(data='List not found.', status=404)

        try:
            email = Email.objects.get(address=address)
            user = email.user
        except Email.DoesNotExist, User.DoesNotExist:
            return response.Response(data='User not found.', status=404)

        membership, created = Membership.objects.get_or_create(mlist=mlist, address=address,
                                                              role=role)
        #membership = Membership(mlist=mlist, address=email, role=role, user=user)
        #membership.save()
        if created:
            serializer = MembershipSerializer(membership)
            return response.Response(data=serializer.data, status=201)
        else:
            return response.Response(data='Already Exists', status=400)


class MailingListViewSet(BaseModelViewSet):

    queryset = MailingList.objects.all()
    serializer_class = MailingListSerializer
    filter_fields = ('list_name', 'fqdn_listname', 'mail_host',)

    def list(self, request):
        """Don't list memberships in the list view"""
        queryset = self.queryset
        serializer = MailingListDetailSerializer(queryset, many=True)
        return response.Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Memberships are listed here in detail view"""
        queryset = self.queryset
        mlist = get_object_or_404(queryset, pk=pk)
        serializer = MailingListSerializer(mlist)
        return response.Response(serializer.data)

    def create(self, request):
        """
        Create a new MailingList on the domain
        provided in POST parameters.
        """
        try:
            domain = Domain.objects.get(mail_host=request.POST['mail_host'])
        except Domain.DoesNotExist:
            return response.Response(data='Domain not found', status=404)
        mlist = domain.create_list(request.POST['list_name'])
        serializer = MailingListSerializer(mlist)
        return response.Response(serializer.data, status=201)


class ListSettingsViewSet(BaseModelViewSet):
    queryset = ListSettings.objects.all()
    serializer_class = ListSettingsSerializer


class DomainViewSet(BaseModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer

