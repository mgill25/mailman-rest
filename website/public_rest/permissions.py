#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from public_rest.models import Membership
from rest_framework import permissions

logger = logging.getLogger(__name__)

class IsValidMembershipPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        """
        For a given user, permission should be given if
        the user has a membership that allows her access to
        the objects related to it (lists, memberships, etc)
        """
        # Jane has 2 memberships, one as a moderator and another as
        # a member. How to ensure that she would have permissions
        # for the first and not the second?
        user = request.user
        logger.debug("-------------------------")
        logger.debug("Incoming obj: {0}".format(obj))
        logger.debug("Incoming user: {0}".format(user))
        logger.debug("-------------------------")
        memberships = Membership.objects.filter(user=user)
        if memberships and memberships.exists():
            return True
        return False

class BaseMembershipPermission(permissions.BasePermission):

    def has_valid_memberships(self, user, role):
        memberships = Membership.objects.filter(user=user, role=role)
        if memberships and memberships.exists():
            return True
        return False

class IsValidModeratorPermission(BaseMembershipPermission):

    def has_permission(self, request, view):
        user = request.user
        return self.has_valid_memberships(user, 'moderator')

class IsValidOwnerPermission(BaseMembershipPermission):

    def has_permission(self, request, view):
        user = request.user
        return self.has_valid_memberships(user, 'owner')

class IsValidMemberPermission(BaseMembershipPermission):

    def has_permission(self, request, view):
        user = request.user
        return self.has_valid_memberships(user, 'member')

