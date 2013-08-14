#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ERROR: Import Loop:
interface -> api -> adaptor -> interface
"""
import re
import json

from base64 import b64encode
from httplib2 import Http
from operator import itemgetter
from urllib import urlencode
from urllib2 import HTTPError
from urlparse import urljoin

from django.db import models


class BaseAdaptor(object):
    """
    An adaptor is a remotely backed object, which will
    contain information that relates back to the lower
    layers via HTTP.

    Getting/Saving an adaptor triggers corresponding
    HTTP requests for the same object (or multiple remote
    objects representing it) at remote.

    The primary link is the `partial_URL` field for every
    remotely backed object.

    """
    #XXX: Save everything or delegate everything or handle per-object?
    layer = 'adaptor'

    def __iter__(self):
        for item in self.iter_fields:
            yield item

class SplitAdaptor(BaseAdaptor):
    """
    An Adaptor layer that splits the data into different locations.
    Object X can be divided into object Y and Z, both being stored
    at different locations.

    Create an object with `local` and `remote` arguments,
    which represent the layers where the fields should be saved.

    `save_local` and `save_remote` represent the functions for saving
    the data at one of those locations. These functions take a list
    of `fields`, which are then saved on the corresponsing object.
    """
    pass


class DomainAdaptor(BaseAdaptor):
    """
    An Adaptor, which does the job of wrapping and unwrapping
    of data b/w the `rest` and `core` layers.
    """
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = None
        self.iter_fields = ['base_url', 'mail_host', 'contact_address', 'description']


    def __repr__(self):
        return '<DomainAdaptor "{0}">'.format(self.mail_host)

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content

    @property
    def url(self):
        self._get_info()
        return self._info['self_link']

    # note: `base_url` property will be renamed to `web_host`
    # in Mailman3Alpha8
    @property
    def base_url(self):
        self._get_info()
        return self._info['base_url']

    @property
    def contact_address(self):
        self._get_info()
        return self._info['contact_address']

    @property
    def description(self):
        self._get_info()
        return self._info['description']

    @property
    def mail_host(self):
        self._get_info()
        return self._info['mail_host']

    @property
    def url_host(self):
        self._get_info()
        return self._info['url_host']

    @property
    def lists(self):
        response, content = self._connection.call(
            'domains/{0}/lists'.format(self.mail_host))
        if 'entries' not in content:
            return []
        return [ListAdaptor(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('fqdn_listname'))]

    def create_list(self, list_name):
        fqdn_listname = '{0}@{1}'.format(list_name, self.mail_host)
        response, content = self._connection.call(
            'lists', dict(fqdn_listname=fqdn_listname))
        return ListAdaptor(self._connection, response['location'])

    def get_or_create(self, listname):
        """Get or create a list"""
        response, content = self._connection.call(
                'domains/{0}/lists'.format(self.mail_host))
        if 'entries' not in content:
            return self.create_list(listname)
        else:
            for entry in content['entries']:
                if entry['list_name'] == listname:
                    return ListAdaptor(self._connection, entry['self_link'])


class AddressAdaptor(BaseAdaptor):
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = {}

    def __repr__(self):
        return '<AddressAdaptor {0}>'.format(self.email)

    def _get_info(self):
        if not self._info:
            response, content = self._connection.call(self._url)
            self._info = content

    @property
    def display_name(self):
        """
        Will only be available for addresses
        associated with users.
        """
        self._get_info()
        return self._info.get('display_name')

    @property
    def registered_on(self):
        self._get_info()
        return self._info.get('registered_on')

    @property
    def verified_on(self):
        self._get_info()
        return self._info.get('verified_on')

    @property
    def email(self):
        self._get_info()
        return self._info.get('email')

    def verify(self):
        self._connection.call('addresses/{0}/verify'
                              .format(self._info['email']), method='POST')
        self._info = None

    def unverify(self):
        self._connection.call('addresses/{0}/unverify'
                              .format(self._info['email']), method='POST')
        self._info = None


class UserAdaptor(BaseAdaptor):
    def __init__(self, connection, url):
        self.connection = connection
        self._url = url
        self._info = {}
        self._addresses = None
        self._subscriptions = None
        self._subscription_list_ids = None
        self._preferences = None
        self._cleartext_password = None

    def __repr__(self):
        return '<User "{0}" ({1})>'.format(
            self.display_name, self.user_id)

    def _get_info(self):
        if not self._info:
            response, content = self.connection.call(self._url)
            self._info = content

    #@property
    #def addresses(self):
    #    return Addresses(self.connection, self.user_id)

    @property
    def display_name(self):
        self._get_info()
        return self._info.get('display_name', None)

    @display_name.setter
    def display_name(self, value):
        self._info['display_name'] = value

    @property
    def password(self):
        self._get_info()
        return self._info.get('password', None)

    @password.setter
    def password(self, value):
        self._cleartext_password = value

    @property
    def user_id(self):
        self._get_info()
        return self._info['user_id']

    @property
    def created_on(self):
        self._get_info()
        return self._info['created_on']

    @property
    def self_link(self):
        self._get_info()
        return self._info['self_link']

    @property
    def subscriptions(self):
        if self._subscriptions is None:
            subscriptions = []
            for address in self.addresses:
                response, content = self.connection.call('members/find',
                    data={'subscriber': address})
                try:
                    for entry in content['entries']:
                        subscriptions.append(_Member(self.connection,
                            entry['self_link']))
                except KeyError:
                    pass
            self._subscriptions = subscriptions
        return self._subscriptions

    @property
    def subscription_list_ids(self):
        if self._subscription_list_ids is None:
            list_ids = []
            for sub in self.subscriptions:
                list_ids.append(sub.list_id)
            self._subscription_list_ids = list_ids
        return self._subscription_list_ids

    @property
    def preferences(self):
        if self._preferences is None:
            path = 'users/{0}/preferences'.format(self.user_id)
            self._preferences = PreferencesAdaptor(self.connection, path)
        return self._preferences

    def save(self):
        data = {'display_name': self.display_name}
        if self._cleartext_password is not None:
            data['cleartext_password'] = self._cleartext_password
        self.cleartext_password = None
        response, content = self.connection.call(self._url,
                                                  data, method='PATCH')
        self._info = None

    def delete(self):
        response, content = self.connection.call(self._url, method='DELETE')


PREFERENCE_FIELDS = (
    'acknowledge_posts',
    'delivery_mode',
    'delivery_status',
    'hide_address',
    'preferred_language',
    'receive_list_copy',
    'receive_own_postings', )


class PreferencesAdaptor(BaseAdaptor):
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._preferences = None
        self.delivery_mode = None
        self._get_preferences()

    def __repr__(self):
        return repr(self._preferences)

    def _get_preferences(self):
        if self._preferences is None:
            response, content = self._connection.call(self._url)
            self._preferences = content
            for key in PREFERENCE_FIELDS:
                self._preferences[key] = content.get(key)

    def __setitem__(self, key, value):
        self._preferences[key] = value

    def __getitem__(self, key):
        return self._preferences[key]

    def __iter__(self):
        for key in self._preferences.keys():
            yield self._preferences[key]

    def __len__(self):
        return len(self._preferences)

    def get(self, key, default=None):
        try:
            return self._preferences[key]
        except KeyError:
            return default

    def keys(self):
        return self._preferences.keys()

    def save(self):
        data = {}
        for key in self._preferences:
            if self._preferences[key] is not None:
                data[key] = self._preferences[key]
        response, content = self._connection.call(self._url, data, 'PUT')



class ListAdaptor(BaseAdaptor):
    def __init__(self, connection, url, data=None):
        self._connection = connection
        self._url = url
        self._info = None
        if data is not None:
            self._info = data

    def __repr__(self):
        return '<List "{0}">'.format(self.fqdn_listname)

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content

    @property
    def owners(self):
        url = self._url + '/roster/owner'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [item['address'] for item in content['entries']]

    @property
    def moderators(self):
        url = self._url + '/roster/moderator'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [item['address'] for item in content['entries']]

    @property
    def fqdn_listname(self):
        self._get_info()
        return self._info['fqdn_listname']

    @property
    def mail_host(self):
        self._get_info()
        return self._info['mail_host']

    @property
    def list_id(self):
        self._get_info()
        return self._info['list_id']

    @property
    def list_name(self):
        self._get_info()
        return self._info['list_name']

    @property
    def display_name(self):
        self._get_info()
        return self._info.get('display_name')

    @property
    def members(self):
        url = 'lists/{0}/roster/member'.format(self.fqdn_listname)
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        return [_Member(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('address'))]

    def get_member_page(self, count=50, page=1):
        url = 'lists/{0}/roster/member'.format(self.fqdn_listname)
        return _Page(self._connection, url, _Member, count, page)

    @property
    def settings(self):
        return SettingsAdaptor(self._connection,
                         'lists/{0}/config'.format(self.fqdn_listname))

    @property
    def held(self):
        """Return a list of dicts with held message information.
        """
        response, content = self._connection.call(
            'lists/{0}/held'.format(self.fqdn_listname), None, 'GET')
        if 'entries' not in content:
            return []
        else:
            entries = []
            for entry in content['entries']:
                msg = dict(hold_date=entry['hold_date'],
                           msg=entry['msg'],
                           reason=entry['reason'],
                           sender=entry['sender'],
                           request_id=entry['request_id'],
                           subject=entry['subject'])
                entries.append(msg)
        return entries

    @property
    def requests(self):
        """Return a list of dicts with subscription requests.
        """
        response, content = self._connection.call(
            'lists/{0}/requests'.format(self.fqdn_listname), None, 'GET')
        if 'entries' not in content:
            return []
        else:
            entries = []
            for entry in content['entries']:
                request = dict(address=entry['address'],
                               delivery_mode=entry['delivery_mode'],
                               display_name=entry['display_name'],
                               language=entry['language'],
                               password=entry['password'],
                               request_id=entry['request_id'],
                               request_date=entry['when'],
                               type=entry['type'])
                entries.append(request)
        return entries

    def add_owner(self, address):
        self.add_role('owner', address)

    def add_moderator(self, address):
        self.add_role('moderator', address)

    def add_role(self, role, address):
        data = dict(list_id=self.list_id,
                    subscriber=address,
                    role=role)
        self._connection.call('members', data)

    def remove_owner(self, address):
        self.remove_role('owner', address)

    def remove_moderator(self, address):
        self.remove_role('moderator', address)

    def remove_role(self, role, address):
        url = 'lists/%s/%s/%s' % (self.fqdn_listname, role, address)
        self._connection.call(url, method='DELETE')

    def moderate_message(self, request_id, action):
        """Moderate a held message.

        :param request_id: Id of the held message.
        :type request_id: Int.
        :param action: Action to perform on held message.
        :type action: String.
        """
        path = 'lists/{0}/held/{1}'.format(self.fqdn_listname,
                                           str(request_id))
        response, content = self._connection.call(path, dict(action=action),
                                                  'POST')
        return response

    def discard_message(self, request_id):
        """Shortcut for moderate_message.
        """
        return self.moderate_message(request_id, 'discard')

    def reject_message(self, request_id):
        """Shortcut for moderate_message.
        """
        return self.moderate_message(request_id, 'reject')

    def defer_message(self, request_id):
        """Shortcut for moderate_message.
        """
        return self.moderate_message(request_id, 'defer')

    def accept_message(self, request_id):
        """Shortcut for moderate_message.
        """
        return self.moderate_message(request_id, 'accept')

    def get_member(self, address):
        """Get a membership.

        :param address: The email address of the member for this list.
        :return: A member proxy object.
        """
        # In order to get the member object we need to
        # iterate over the existing member list
        for member in self.members:
            if member.address == address:
                return member
                break
        else:
            raise ValueError('%s is not a member address of %s' %
                             (address, self.fqdn_listname))

    def subscribe(self, address, display_name=None):
        """Subscribe an email address to a mailing list.

        :param address: Email address to subscribe to the list.
        :type address: str
        :param display_name: The real name of the new member.
        :type display_name: str
        :return: A member proxy object.
        """
        data = dict(
            list_id=self.list_id,
            subscriber=address,
            display_name=display_name,
        )
        response, content = self._connection.call('members', data)
        return _Member(self._connection, response['location'])

    def unsubscribe(self, address):
        """Unsubscribe an email address from a mailing list.

        :param address: The address to unsubscribe.
        """
        # In order to get the member object we need to
        # iterate over the existing member list

        for member in self.members:
            if member.address == address:
                self._connection.call(member.self_link, method='DELETE')
                break
        else:
            raise ValueError('%s is not a member address of %s' %
                             (address, self.fqdn_listname))

    def delete(self):
        response, content = self._connection.call(
            'lists/{0}'.format(self.fqdn_listname), None, 'DELETE')



LIST_READ_ONLY_ATTRS = ('bounces_address', 'created_at', 'digest_last_sent_at',
                        'fqdn_listname', 'http_etag', 'mail_host',
                        'join_address', 'last_post_at', 'leave_address',
                        'list_id', 'list_name', 'next_digest_number',
                        'no_reply_address', 'owner_address', 'post_id',
                        'posting_address', 'request_address', 'scheme',
                        'volume', 'web_host',)

class SettingsAdaptor(BaseAdaptor):
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = {}
        self._get_info()

    def __repr__(self):
        return repr(self._info)

    def _get_info(self):
        if not self._info:
            response, content = self._connection.call(self._url)
            self._info = content

    def __iter__(self):
        for key in self._info.keys():
            yield key

    def __getitem__(self, key):
        return self._info[key]

    def __setitem__(self, key, value):
        self._info[key] = value

    def __len__(self):
        return len(self._info)

    def get(self, key, default=None):
        try:
            return self._info[key]
        except KeyError:
            return default

    def keys(self):
        return self._info.keys()

    def save(self):
        data = {}
        for attribute, value in self._info.items():
            if attribute not in LIST_READ_ONLY_ATTRS:
                data[attribute] = value
        response, content = self._connection.call(self._url, data, 'PATCH')


