#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import requests
from django.conf import settings


"""
Some utility functions
"""
# A Handy function
def call_api(url, method_name='GET', data={}):
    # TODO: Move with other HTTP-related code.
    logger = logging.getLogger('HTTP')
    method_name.lower()
    method = getattr(requests, method_name, None)
    if method:
        if method_name == 'get' or method_name == 'delete':
            logger.info("{0} {1}".format(method_name, url))
            response = method(url, auth=(settings.MAILMAN_USER, settings.MAILMAN_PASS))
        else:
            logger.info("{0} {1} {2}".format(method_name, url, data))
            response = method(url, data, auth=(settings.MAILMAN_USER, settings.MAILMAN_PASS))
        logger.debug("Status {0}: {1}".format(response.status_code, response.content))
        return response.status_code, response.content


def get_related_attribute(instance, attr_string):
    """
    For the Django model Membership, which has a ForeignKey to
    the User model, it goes something like this:
        >>> mem = Membership.objects.all()[0]
        >>> get_related_attributes(mem, 'user.display_name')
        u'Tony Stark'
    """
    attr_string_list = attr_string.split('.')
    primary_attr = attr_string_list[0]
    attribute = getattr(instance, primary_attr)
    if len(attr_string_list) > 1:
        for sub_strings in attr_string_list[1:]:
            attribute = getattr(attribute, sub_strings)
    return attribute

