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

class ListPaginatorSerializer(serializers.Serializer):
    next = pagination.NextPageField(source='*')
    prev = pagination.PreviousPageField(source='*')


#################################################################
# Primary Model Serializers
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

    total_results = serializers.Field(source='paginator.count')
    results_field = 'objects'

    #XXX: mail_host should only be writable at creation time.
    # Read-only
    members = serializers.Field('members')
    owners = serializers.Field('owners')
    moderators = serializers.Field('moderators')
    fqdn_listname = serializers.Field('fqdn_listname')
    #membership_set = _PartialMembershipSerializer(many=True)
    #membership_listing = serializers.HyperlinkedIdentityField(
    #        view_name='membership-detail',
    #        lookup_field='fqdn_listname'
    #)

    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname', 'list_name', 'mail_host',
                'membership_set', 'settings',
                #'membership_listing',
                #'members', 'owners', 'moderators',
                )

class MailingListDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MailingList
        fields = ('url', 'fqdn_listname', 'list_name', 'mail_host',
                'settings')


class ListSettingsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ListSettings
        exclude = ('partial_URL', 'id', 'http_etag', 'acceptablealias')



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
