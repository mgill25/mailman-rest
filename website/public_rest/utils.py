#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from django.conf import settings


"""
Some utility functions
"""

def get_related_attribute(instance, attr_string):
    """
    For the Django model Membership, which has a ForeignKey to
    the User model, it goes something like this:
        >>> mem = Membership.objects.all()[0]
        >>> get_related_attribute(mem, 'user.display_name')
        u'Tony Stark'
    """
    attr_string_list = attr_string.split('.')
    primary_attr = attr_string_list[0]
    attribute = getattr(instance, primary_attr, None)
    if len(attr_string_list) > 1:
        for sub_strings in attr_string_list[1:]:
            attribute = getattr(attribute, sub_strings, None)
    return attribute

