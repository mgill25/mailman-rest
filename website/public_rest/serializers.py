from rest_framework import serializers
from public_rest.models import MailingList, Membership, User, Domain, Email


class UserSerializer(serializers.HyperlinkedModelSerializer):
    emails = serializers.RelatedField(many=True)

    class Meta:
        model = User
        fields = ('url', 'display_name', 'emails', 'is_superuser',
                'preferred_email'
                #'membership_set',
                )


class MembershipSerializer(serializers.HyperlinkedModelSerializer):

    is_owner = serializers.Field('is_owner')
    is_moderator = serializers.Field('is_moderator')

    class Meta:
        model = Membership
        fields = ('url', 'address', 'role', 'user', 'mlist',
                'is_owner', 'is_moderator')

class _PartialMembershipSerializer(serializers.HyperlinkedModelSerializer):
    """Partial serializer for nested representations."""
    class Meta:
        model = Membership
        fields = ('url', 'address')


class MailingListSerializer(serializers.HyperlinkedModelSerializer):

    #XXX: mail_host should only be writable at creation time.
    # Read-only
    members = serializers.Field('members')
    owners = serializers.Field('owners')
    moderators = serializers.Field('moderators')
    fqdn_listname = serializers.Field('fqdn_listname')
    membership_set = _PartialMembershipSerializer(many=True)
    #membership_listing = serializers.HyperlinkedIdentityField(view_name='membership-list')

    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname', 'list_name', 'mail_host',
                'membership_set',
                #'membership_listing',
                #'members', 'owners', 'moderators',
                )


class _PartialMailingListSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname')


class DomainSerializer(serializers.HyperlinkedModelSerializer):
    #mailinglist_listing = serializers.HyperlinkedIdentityField(view_name='mailinglist-list')
    mailinglist_set = _PartialMailingListSerializer(many=True)
    class Meta:
        model = Domain
        fields = ('base_url', 'mail_host', 'contact_address', 'description', 'mailinglist_set')


class EmailSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.RelatedField()

    class Meta:
        model = Email
        fields = ('url', 'address', 'user', 'verified')
