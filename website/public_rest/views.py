import logging

from django.contrib.auth.models import Group
from rest_framework import viewsets, response
from rest_framework.filters import SearchFilter

from .serializers import UserSerializer, MembershipSerializer, \
        MailingListSerializer, DomainSerializer, EmailSerializer

from .models import User, Membership, MailingList, Domain, Email

#logging
logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.all()

        logger.debug("QUERY_PARAMS: {0}".format(self.request.QUERY_PARAMS))

        display_name = self.request.QUERY_PARAMS.get('display_name', None)
        email = self.request.QUERY_PARAMS.get('email', None)
        # now filter out query params
        if display_name is not None:
            queryset = queryset.filter(display_name=display_name)
        if email is not None:
            queryset = queryset.filter(email__address=email)
            verified = self.request.QUERY_PARAMS.get('verified', None)
            if verified is not None:
                queryset = queryset.filter(email__verified=verified)

        return queryset


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    filter_fields = ('user', 'address', 'verified',)
    #filter_backends = (SearchFilter, )
    #search_fields = ('user__display_name', )


class MembershipViewSet(viewsets.ModelViewSet):

    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer


class MailingListViewSet(viewsets.ModelViewSet):

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


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer

