#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json

from base64 import b64encode
from httplib2 import Http
from operator import itemgetter
from urllib import urlencode
from urllib2 import HTTPError
from urlparse import urljoin


__version__ = '0.01'

class MailmanConnectionError(Exception):
    """Custom exception to catch Connection errors"""
    pass

class Connection:
    """A connection to the REST client."""

    def __init__(self, baseurl, name=None, password=None):
        """Initialize a connection to the REST API.

        :param baseurl: The base url to access the Mailman 3 REST API.
        :param name: The Basic Auth user name.  If given, the `password` must
            also be given.
        :param password: The Basic Auth password.  If given the `name` must
            also be given.
        """
        if baseurl[-1] != '/':
            baseurl += '/'
        self.baseurl = baseurl
        self.name = name
        self.password = password
        if name is not None and password is None:
            raise TypeError('`password` is required when `name` is given')
        if name is None and password is not None:
            raise TypeError('`name` is required when `password` is given')
        if name is None:
            self.basic_auth = None
        else:
            auth = '{0}:{1}'.format(name, password)
            self.basic_auth = b64encode(auth)

    def call(self, path, data=None, method=None):
        """Make a call to the Mailman REST API.

        :param path: The url path to the resource.
        :type path: str
        :param data: Data to send, implies POST (default) or PUT.
        :type data: dict
        :param method: The HTTP method to call.  Defaults to GET when `data`
            is None or POST if `data` is given.
        :type method: str
        :return: The response content, which will be None, a dictionary, or a
            list depending on the actual JSON type returned.
        :rtype: None, list, dict
        :raises HTTPError: when a non-2xx status code is returned.
        """
        headers = {
            'User-Agent': 'GNU Mailman REST client v{0}'.format(__version__),
        }
        if data is not None:
            data = urlencode(data, doseq=True)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if method is None:
            if data is None:
                method = 'GET'
            else:
                method = 'POST'
        method = method.upper()
        if self.basic_auth:
            headers['Authorization'] = 'Basic ' + self.basic_auth
        url = urljoin(self.baseurl, path)
        try:
            response, content = Http().request(url, method, data, headers)
            # If we did not get a 2xx status code, make this look like a
            # urllib2 exception, for backward compatibility.
            if response.status // 100 != 2:
                raise HTTPError(url, response.status, content, response, None)
            if len(content) == 0:
                return response, None
            # XXX Work around for http://bugs.python.org/issue10038
            content = unicode(content)
            return response, json.loads(content)
        except HTTPError:
            raise
        except IOError:
            raise MailmanConnectionError('Could not connect to Mailman API')

class Interface(object):
    """
    An Interface to connect to the Core
    """

    def __init__(self, baseurl, name=None, password=None):
        self.connection = Connection(baseurl, name=name, password=password)

    def __repr__(self):
        return '<Interface {0.baseurl} ({0.name}:{0.password})>'.format(self.connection)

    @property
    def system(self):
        return self.connection.call('system')[1]

    @property
    def users(self):
        response, content = self.connection.call('users')
        if 'entries' not in content:
            return []
        return [_User(self.connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('self_link'))]

    def get_user(self, address):
        response, content = self.connection.call(
            'users/{0}'.format(address))
        return _User(self.connection, content['self_link'])

    def create_user(self, email, password, display_name=''):
        response, content = self.connection.call(
            'users', dict(email=email, password=password,
                          display_name=display_name))
        return _User(self.connection, response['location'])

    @property
    def lists(self):
        response, content = self.connection.call('lists')
        if 'entries' not in content:
            return []
        return [_List(self.connection, entry['self_link'])
                for entry in content['entries']]

    @property
    def domains(self):
        response, content = self.connection.call('domains')
        if 'entries' not in content:
            return []
        return [_Domain(self.connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('url_host'))]

    def get_domain(self, mail_host=None, web_host=None):
        """Get domain by its mail_host or its web_host."""
        if mail_host is not None:
            response, content = self.connection.call(
                'domains/{0}'.format(mail_host))
            return _Domain(self.connection, content['self_link'])
        elif web_host is not None:
            for domain in self.domains:
                # note: `base_url` property will be renamed to `web_host`
                # in Mailman3Alpha8
                if domain.base_url == web_host:
                    return domain
                    break
            else:
                return None


class _User(object):
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
    #    return _Addresses(self.connection, self.user_id)

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
            self._preferences = _Preferences(self.connection, path)
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


class _Preferences:
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

class _Domain:
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = None

    def __repr__(self):
        return '<Domain "{0}">'.format(self.mail_host)

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content

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
        return [_List(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('fqdn_listname'))]

    def create_list(self, list_name):
        fqdn_listname = '{0}@{1}'.format(list_name, self.mail_host)
        response, content = self._connection.call(
            'lists', dict(fqdn_listname=fqdn_listname))
        return _List(self._connection, response['location'])

    def get_or_create(self, listname):
        """Get or create a list"""
        response, content = self._connection.call(
                'domains/{0}/lists'.format(self.mail_host))
        if 'entries' not in content:
            return self.create_list(listname)
        else:
            for entry in content['entries']:
                if entry['list_name'] == listname:
                    return _List(self._connection, entry['self_link'])


class _List:
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
        return _Settings(self._connection,
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

class _Settings:
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = None
        self._get_info()

    def __repr__(self):
        return repr(self._info)

    def _get_info(self):
        if self._info is None:
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


