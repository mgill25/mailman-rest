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


class _User(object):
    def __init__(self, connection, url):
        self.connection = connection
        self._url = url
        self._info = None
        self._addresses = None
        self._subscriptions = None
        self._subscription_list_ids = None
        self._preferences = None
        self._cleartext_password = None

    def __repr__(self):
        return '<User "{0}" ({1})>'.format(
            self.display_name, self.user_id)

    def _get_info(self):
        if self._info is None:
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


