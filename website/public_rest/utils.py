#!/usr/bin/env python
# -*- coding: utf-8 -*-
from functools import wraps
from django.conf import settings
from django.core.exceptions import PermissionDenied
import logging


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

def is_list_staff(user, mlist):
    user_mails = [email for email in user.emails]
    owner_mails = [mem.address for mem in mlist.owners]
    mod_mails = [mem.address for mem in mlist.moderators]
    common = [email for email in user_mails if
    email in owner_mails or email in mod_mails]
    if len(common) != 0:
        return True
    return False

def make_permission(check_func):
    """
    Use this decorator to create permissions.
    A permission function should always return a bool.
    """
    def _wrap_checker(view_func):
        @wraps(view_func)
        def _checker(*args, **kwargs):
            if check_func(*args, **kwargs):
                return view_func(*args, **kwargs)
            else:
                raise PermissionDenied
        return _checker
    return _wrap_checker
