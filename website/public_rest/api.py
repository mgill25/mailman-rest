#!/usr/bin/env python
import logging
import requests
from operator import itemgetter
from urlparse import urljoin, urlsplit

from django.conf import settings
from django.db.models.loading import get_model

from public_rest.adaptors import *

__version__ = '0.1'

# Get an instance of a logger
logger = logging.getLogger('api_http')


class MailmanConnectionError(Exception):
    """Custom exception to catch Connection errors"""
    pass

class Connection(object):
    """A connection to the REST client."""

    def __repr__(self):
        return self.base_url

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
            #print('url: {0}, base_url: {1}, path: {2}'.format(url, self.base_url, path))
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

    def get_email(self, address=None):
        if address is not None:
            response, content = self.connection.call(
                    'addresses/{0}'.format(address))
            return AddressAdaptor(self.connection, content['self_link'])


    def get_listsettings(self, fqdn_listname):
        if fqdn_listname is not None:
            response, content = self.connection.call(
                    'lists/{0}/config'.format(fqdn_listname))
            return SettingsAdaptor(self.connection)

    def get_mailinglist(self, fqdn_listname):
        if fqdn_listname is not None:
            response, content = self.connection.call(
                'lists/{fqdn_listname}'.format(fqdn_listname=fqdn_listname))
            return ListAdaptor(self.connection, content['self_link'])

    # Some generic functions
    def get_model_from_object(self, object_type):
        return get_model(__file__.split('/')[-2], object_type)

    def get_object_from_url(self, partial_url, object_type):
        if partial_url and object_type:
            model = self.get_model_from_object(object_type)
            return model.adaptor(self.connection, partial_url)

    def get_object(self, partial_url=None, object_type=None, **kwargs):
        """
        :kwargs - Data arguments for `get_` functions.
        """
        if partial_url and object_type:
            return self.get_object_from_url(partial_url=partial_url, object_type=object_type)
        elif kwargs and object_type and not partial_url:
            imethod = getattr(self, 'get_' + object_type)
            rv = imethod(**kwargs)
            return rv

    def get_all_from_url(self, url, object_type):
        """
        Get all objects and return an adaptor list.
        """
        response, content = self.connection.call(urlsplit(url).path)
        if 'entries' not in content:
            return []

        if object_type == 'domain':
            sort_key = itemgetter('url_host')
        elif object_type == 'user':
            sort_key = itemgetter('self_link')
        else:
            sort_key = None
        model = self.get_model_from_object(object_type)
        return [model.adaptor(self.connection, entry['self_link'])
                        for entry in sorted(content['entries'],
                                    key=sort_key)]

    def get_api_endpoint(self, object_type, **kwargs):
        """
        For a given object type, get the API endpoint
        that we must call.
        :Domain has `/domains` endpoint and `domain` object type.
        :Email has `/addresses` endpoint and `email` object type.
        """
        if object_type == 'email':
            endpoint = 'addresses'
        elif object_type == 'listsettings':
            endpoint = 'lists/{0}/config'.format(kwargs['fqdn_listname'])
        elif object_type == 'mailinglist':
            endpoint = 'lists'
        else:
            endpoint = object_type + 's'
        return endpoint

    def create_object(self, object_type=None, data=None, **kwargs):
        """
        Create a Remote object and return the adaptor.
        """
        # Each adaptor has its own way of representing
        # the data. It *might* be the case that an adaptor X
        # is represented by different objects Y and Z at the
        # Mailman Core API.
        endpoint = self.get_api_endpoint(object_type, **kwargs)
        response, content = self.connection.call(endpoint, data=data, method='POST')
        partial_url = urlsplit(response['location']).path
        model = self.get_model_from_object(object_type)
        return model.adaptor(self.connection, partial_url)

    def update_object(self, partial_url=None, data=None):
        """
        `PATCH` the API to update objects (If method allowed)
        """
        response, content = self.connection.call(partial_url, data=data, method='PATCH')
        model = self.get_model_from_object(object_type)
        return model.adaptor(self.connection, partial_url)
