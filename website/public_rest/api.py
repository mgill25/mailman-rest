#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Get responses from Mailman Core and use adaptors to
wrap them up.

    >> from api import get_from_interface
    >> given_url = 'http://localhost:8001/3.0/users/'
    >> response = get_from_interface(partial_url=given_url, method='GET')
    >> response.status_code
    200
    >> response.json
    { "username" : "Foobar", "email_addresses" : "foo@example.com" }
"""

import logging
import requests
from urlparse import urljoin

from django.conf import settings

from public_rest.adaptors import *

__version__ = '0.1'

# Get an instance of a logger
logger = logging.getLogger('api_http')


class MailmanConnectionError(Exception):
    """Custom exception to catch Connection errors"""
    pass

class Connection:
    """A connection to the REST client."""

    def __init__(self, base_url=None, name=None, password=None):
        """Initialize a connection to the REST API.

        :param base_url: The base url to access the Mailman 3 REST API.
        :param name: The Basic Auth user name.  If given, the `password` must
            also be given.
        :param password: The Basic Auth password.  If given the `name` must
            also be given.
        """
        if base_url is None:
            base_url = '{base}/3.0/'.format(base=settings.MAILMAN_API_URL)
        if base_url[-1] != '/':
            base_url += '/'
        self.base_url = base_url
        self.name = name
        if not self.name:
            self.name = settings.MAILMAN_USER
        self.password = password
        if not self.password:
            self.password = settings.MAILMAN_PASS
        if self.name is None:
            self.basic_auth = None
        else:
            auth = '{0}:{1}'.format(self.name, self.password)
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
        url = urljoin(self.base_url, path)
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


class CoreInterface(object):
    """
    An Interface to connect to the Core
    """

    def __init__(self, base_url=None):
        self.base_url = base_url
        self.connection = Connection(base_url=self.base_url)

    def __repr__(self):
        return '<CoreInterface {0.base_url} >'.format(self.connection)

    def get_from_url(self, url):
        """
        Generic function. Get response from the API and wrap it using proxy objects.
        """
        if 'users' in url:
            return UserAdaptor(self.connection, url)
        elif 'lists' in url:
            return ListAdaptor(self.connection, url)

    @property
    def system(self):
        return self.connection.call('system')[1]

    @property
    def users(self):
        response, content = self.connection.call('users')
        if 'entries' not in content:
            return []
        return [UserAdaptor(self.connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('self_link'))]

    def get_user(self, address):
        response, content = self.connection.call(
            'users/{0}'.format(address))
        return UserAdaptor(self.connection, content['self_link'])

    def create_user(self, email, password, display_name=''):
        response, content = self.connection.call(
            'users', dict(email=email, password=password,
                          display_name=display_name))
        return UserAdaptor(self.connection, response['location'])

    @property
    def lists(self):
        response, content = self.connection.call('lists')
        if 'entries' not in content:
            return []
        return [ListAdaptor(self.connection, entry['self_link'])
                for entry in content['entries']]

    @property
    def domains(self):
        response, content = self.connection.call('domains')
        if 'entries' not in content:
            return []
        return [DomainAdaptor(self.connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('url_host'))]

    def get_domain(self, mail_host=None, web_host=None):
        """Get domain by its mail_host or its web_host."""
        if mail_host is not None:
            response, content = self.connection.call(
                'domains/{0}'.format(mail_host))
            return DomainAdaptor(self.connection, content['self_link'])
        elif web_host is not None:
            for domain in self.domains:
                # note: `base_url` property will be renamed to `web_host`
                # in Mailman3Alpha8
                if domain.base_url == web_host:
                    return domain
                    break
            else:
                return None


