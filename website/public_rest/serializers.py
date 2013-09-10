from rest_framework import pagination
from rest_framework import serializers
from public_rest.models import *


# Partial or Support Serializers
class _PartialMembershipSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Membership
        fields = ('url', 'address')


class _PartialMailingListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname')


#################################################################

# Primary Model Serializers
class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ('url', 'display_name', 'is_superuser',
                'preferred_email',
                )


class UserDetailSerializer(serializers.HyperlinkedModelSerializer):
    emails = serializers.RelatedField(many=True)
    membership_set = _PartialMembershipSerializer(many=True)

    class Meta:
        model = User
        fields = ('url', 'display_name', 'is_superuser', 'emails',
                  'preferred_email',
                  'membership_set',
                )


class MembershipListSerializer(serializers.HyperlinkedModelSerializer):

    mlist = serializers.RelatedField()
    user = serializers.RelatedField()

    class Meta:
        model = Membership
        fields = ('url', 'address', 'role', 'user', 'mlist',)


class MembershipDetailSerializer(serializers.HyperlinkedModelSerializer):
    mlist = _PartialMailingListSerializer()
    user = serializers.HyperlinkedIdentityField(view_name='user-detail')

    class Meta:
        model = Membership
        fields = ('url', 'address', 'role', 'user', 'mlist',)


class PaginatedMembershipDetailSerializer(pagination.PaginationSerializer):

    class Meta:
        object_serializer_class = MembershipListSerializer


class ListSettingsSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ListSettings
        exclude = ('partial_URL', 'id', 'http_etag', 'acceptablealias')


class MailingListSerializer(serializers.HyperlinkedModelSerializer):
    """Summary of a Mailing List"""
    #XXX: mail_host should only be writable at creation time.
    # Read-only
    fqdn_listname = serializers.Field('fqdn_listname')

    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname', 'list_name', 'mail_host')


class MailingListDetailSerializer(serializers.HyperlinkedModelSerializer):
    """Details of a Mailing List"""
    members = serializers.Field('members')
    owners = serializers.Field('owners')
    moderators = serializers.Field('moderators')
    # membership_set = _PartialMembershipSerializer(many=True, read_only=True)
    settings = serializers.HyperlinkedIdentityField(view_name='listsettings-detail')

    #membership_listing = serializers.HyperlinkedIdentityField(
    #           view_name='membership-detail',
    #           lookup_field='fqdn_listname'
    #)


    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname', 'list_name', 'mail_host',
                  'members', 'owners', 'moderators',
                  #'membership_listing',
                  'settings',
                  )


class DomainSerializer(serializers.HyperlinkedModelSerializer):
    #mailinglist_listing = serializers.HyperlinkedIdentityField(view_name='mailinglist-list')

    class Meta:
        model = Domain
        fields = ('url', 'base_url', 'mail_host',)


class DomainDetailSerializer(serializers.HyperlinkedModelSerializer):
    mailinglist_set = _PartialMailingListSerializer(many=True,read_only=True)

    class Meta:
        model = Domain
        fields = ('url', 'base_url', 'mail_host', 'contact_address',
                'description', 'mailinglist_set')


class EmailSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.RelatedField()

    class Meta:
        model = Email
        fields = ('url', 'address', 'user', 'verified')
