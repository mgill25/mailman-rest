from django.contrib.auth.models import Group
from rest_framework import viewsets

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


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
