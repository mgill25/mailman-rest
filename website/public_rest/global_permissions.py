#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import make_permission, is_list_staff

@make_permission
def DenyAll(*args, **kwargs):
    return False

@make_permission
def IsOwnerOrModeratorPermission(*args, **kwargs):
    request = kwargs.get('request', None)
    mlist = kwargs.get('mlist', None)
    if request.user and mlist:
        if utils.is_list_staff(request.user, mlist):
            return True
    return False

