import logging

from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework.decorators import link, action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser

from public_rest.serializers import *
from public_rest.models import *
from public_rest.permissions import *

#logging
logger = logging.getLogger(__name__)


class BaseModelViewSet(ModelViewSet):
    def str2bool(self, s):
        return s.lower() in ['true']

    def is_boolean_string(self, s):
        return s.lower() in ['true', 'false']

class UserViewSet(BaseModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(methods=['POST', 'GET'])
    def emails(self, request, *args, **kwargs):
        user = self.get_object()

        if request.method == 'POST':
            email = user.add_email(request.DATA.get('address'))
            if email:
                serializer = EmailSerializer(email, context={'request': request})
                return Response(serializer.data, status=201)
        elif request.method == 'GET':
            serializer = EmailSerializer(user.emails,
                                        many=True,
                                        context={'request': request})
            return Response(serializer.data, status=200)

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

    def create(self, request):
        display_name = request.DATA.get('display_name')
        email = request.DATA.get('email')
        password = request.DATA.get('password')

        if not display_name or not email or not password:
            return Response(data='Incomplete data', status=400)

        try:
            user = User.objects.get(display_name=display_name)
            if user:
                return Response(data='Already Exists', status=400)
            #TODO: Handle email-already-exists
        except User.DoesNotExist:
            user = User.objects.create(display_name=display_name, email=email, password=password)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=201)


class EmailViewSet(BaseModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    filter_fields = ('user', 'address', 'verified',)
    permission_classes = [IsAdminUser]

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

        self.queryset = queryset
        return super(EmailViewSet, self).get_queryset()


class MembershipViewSet(BaseModelViewSet):

    queryset = Membership.objects.all()
    serializer_class = MembershipListSerializer
    permission_classes = [IsAdminUser,]
    filter_fields = ('role', 'user',)

    def create(self, request):
        """Membership creation"""
        role = request.DATA.get('role')
        list_name = request.DATA.get('mlist')
        address = request.DATA.get('address')

        try:
            mlist = MailingList.objects.get(fqdn_listname=list_name)
            logger.debug("List found! {0}".format(mlist))
        except MailingList.DoesNotExist:
            return Response(data='List not found.', status=404)

        try:
            email = Email.objects.get(address=address)
            user = email.user
        except Email.DoesNotExist, User.DoesNotExist:
            return Response(data='User not found.', status=404)

        #membership, created = Membership.objects.get_or_create(mlist=mlist, address=address,
        #                                                      role=role)
        membership = Membership(mlist=mlist, address=email, role=role, user=user)
        membership.save()
        if created:
            serializer = MembershipSerializer(membership, context={'request': request})
            return Response(data=serializer.data, status=201)
        else:
            return Response(data='Already Exists', status=400)

    def retrieve(self, request, pk=None):
        queryset = self.queryset
        membership = get_object_or_404(queryset, pk=pk)
        serializer = MembershipDetailSerializer(membership,
                        context={'request': request})
        return Response(serializer.data)


class MailingListViewSet(BaseModelViewSet):

    queryset = MailingList.objects.all()
    serializer_class = MailingListSerializer
    #filter_fields = ('list_name', 'fqdn_listname', 'mail_host',)

    def get_queryset(self):
        #XXX: not working
        queryset = self.queryset
        list_name = self.request.QUERY_PARAMS.get('list_name', None)
        fqdn_listname = self.request.QUERY_PARAMS.get('fqdn_listname', None)
        mail_host = self.request.QUERY_PARAMS.get('mail_host', None)

        if list_name is not None:
            queryset = self.queryset.filter(list_name=list_name)
        if fqdn_listname is not None:
            queryset = self.queryset.filter(fqdn_listname=fqdn_listname)
        if mail_host is not None:
            queryset = self.queryset.filter(mail_host=mail_host)

        self.queryset = queryset
        return super(MailingListViewSet, self).get_queryset()

    #def list(self, request):
    #    """Don't list memberships in the list view"""
    #    queryset = self.queryset
    #    serializer = MailingListDetailSerializer(queryset,
    #            many=True,
    #            context={'request': request})
    #    return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Memberships are listed here in detail view"""
        queryset = self.queryset
        mlist = get_object_or_404(queryset, pk=pk)
        serializer = MailingListDetailSerializer(mlist,
                        context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new MailingList on the domain
        provided in POST (DATA) parameters.
        """
        mail_host = request.DATA.get('mail_host')
        list_name = request.DATA.get('list_name')
        if not mail_host or not list_name:
            return Response('Incomplete data', status=400)

        try:
            domain = Domain.objects.get(mail_host=mail_host)
        except Domain.DoesNotExist:
            return Response(data='Domain not found', status=404)

        mlist = domain.create_list(request.DATA['list_name'])
        # TODO: When created, every list must have an owner
        mlist.add_owner(request.user.preferred_email.address)
        serializer = MailingListSerializer(mlist,
                context={'request': request})
        return Response(serializer.data, status=201)


class ListSettingsViewSet(BaseModelViewSet):
    queryset = ListSettings.objects.all()
    serializer_class = ListSettingsSerializer

    def get_object(self):
        queryset = self.get_queryset()
        filter = {}
        filter['mailinglist__id'] = self.kwargs['pk']
        obj = get_object_or_404(queryset, **filter)
        #logger.debug("***********************************")
        #logger.debug("List Setting Object: {0}".format(obj))
        #logger.debug("***********************************")
        return obj

    def partial_update(self, request, *args, **kwargs):
        """ Handle PATCH """
        obj = self.get_object()

        try:
            for key, val in request.DATA.items():
                if self.is_boolean_string(key):
                    setattr(obj, key, self.str2bool(val))
                else:
                    setattr(obj, key, val)
            obj.save()
        except Exception as e:
            logger.debug("Exception:::{0} - {1}".format(e, type(e)))
            return Response('Failed', status=500)
        else:
            return Response('Updated', status=204)

class DomainViewSet(BaseModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer

