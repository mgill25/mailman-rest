from django.contrib.auth.models import Group
from rest_framework import viewsets, response

from .serializers import UserSerializer, MembershipSerializer, \
        MailingListSerializer, DomainSerializer, EmailSerializer

from .models import User, Membership, MailingList, Domain, Email


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


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


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
