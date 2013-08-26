from rest_framework import serializers
from public_rest.models import *


# Partial Serializers
class _PartialMembershipSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Membership
        fields = ('url', 'address')


class _PartialMailingListSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname')


# Full Serializers
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
    #mlist = serializers.RelatedField()
    mlist = _PartialMailingListSerializer()
    user = serializers.RelatedField()

    class Meta:
        model = Membership
        fields = ('url', 'address', 'role', 'user', 'mlist',
                'is_owner', 'is_moderator', )


class MailingListSerializer(serializers.HyperlinkedModelSerializer):

    #XXX: mail_host should only be writable at creation time.
    # Read-only
    members = serializers.Field('members')
    owners = serializers.Field('owners')
    moderators = serializers.Field('moderators')
    fqdn_listname = serializers.Field('fqdn_listname')
    settings = serializers.RelatedField()
    membership_set = _PartialMembershipSerializer(many=True)
    #membership_listing = serializers.HyperlinkedIdentityField(view_name='membership-list')

    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname', 'list_name', 'mail_host',
                'membership_set', 'settings',
                #'membership_listing',
                #'members', 'owners', 'moderators',
                )


class ListSettingsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ListSettings
        fields = tuple([fn for fn in ListSettings._meta.get_all_field_names()
                        if fn != 'id' or fn != 'partial_URL'
                       ])


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
