import logging

from django.contrib.auth.models import Group
from rest_framework import viewsets, response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser

from .serializers import UserSerializer, MembershipSerializer, \
        MailingListSerializer, DomainSerializer, EmailSerializer

from public_rest.models import User, Membership, MailingList, Domain, Email
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


class MailingListViewSet(BaseModelViewSet):

    queryset = MailingList.objects.all()
    serializer_class = MailingListSerializer

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
        return response.Response(serializer.data)


class DomainViewSet(BaseModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer

