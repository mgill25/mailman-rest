#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from public_rest.models import Membership
from rest_framework import permissions

logger = logging.getLogger(__name__)

class BaseMembershipPermission(permissions.BasePermission):
    """
    Authentication is necessary.
    """
    def has_valid_memberships(self, request, user, role):
        #TODO: Even in the case of empty memberships, we can grant permission.
        logger.debug("Incoming user: {0}".format(user, type(user)))
        if user and user.is_authenticated():
            memberships = Membership.objects.filter(user=user, role=role)
            if memberships and memberships.exists():
                return True
        return False


class IsValidModeratorPermission(BaseMembershipPermission):

    def has_permission(self, request, view):
        user = request.user
        return self.has_valid_memberships(request, user, 'moderator')


class IsValidOwnerPermission(BaseMembershipPermission):

    def has_permission(self, request, view):
        user = request.user
        return self.has_valid_memberships(request, user, 'owner')


class IsValidMemberPermission(BaseMembershipPermission):

    def has_permission(self, request, view):
        user = request.user
        return self.has_valid_memberships(request, user, 'member')


class IsOwnerOrModeratorPermission(BaseMembershipPermission):

    def has_permission(self, request, view):
        user = request.user
        is_owner = self.has_valid_memberships(request, user, 'owner')
        is_moderator = self.has_valid_memberships(request, user, 'moderator')
        return is_owner or is_moderator


class IsOwnerOrReadOnlyPermission(BaseMembershipPermission):

    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        return self.has_valid_memberships(request, user, 'owner')


class IsMemberOrReadOnlyPermission(BaseMembershipPermission):

    def has_permission(self, request, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        return self.has_valid_memberships(request, user, 'member')


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return True

        elif request.user and request.user.is_staff:
            return True
        return False
