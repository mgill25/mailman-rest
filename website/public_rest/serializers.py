from rest_framework import serializers
from public_rest.models import MailingList, Membership, User, Domain


class UserSerializer(serializers.HyperlinkedModelSerializer):

    emails = serializers.RelatedField(many=True)

    class Meta:
        model = User
        fields = ('url', 'display_name', 'emails',
                'is_superuser', 'membership_set')


class MembershipSerializer(serializers.HyperlinkedModelSerializer):

    is_owner = serializers.Field('is_owner')
    is_moderator = serializers.Field('is_moderator')

    class Meta:
        model = Membership
        fields = ('url', 'address', 'role', 'user', 'mlist',
                'is_owner', 'is_moderator')


class MailingListSerializer(serializers.HyperlinkedModelSerializer):

    members = serializers.Field('members')
    owners = serializers.Field('owners')
    moderators = serializers.Field('moderators')

    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname', 'list_name', 'mail_host',
                'display_name', 'members', 'owners', 'moderators' )


