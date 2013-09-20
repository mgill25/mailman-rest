#!/usr/bin/env python
# -*- coding: utf-8 -*-
# View-based access policies.

from public_rest.permissions import *
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser

# User
class UserViewPolicy(IsAdminOrReadOnly):
    pass


class UserEmailPolicy(IsOwnerOrModeratorPermission):
    pass


class UserSubscriptionPolicy(IsOwnerOrModeratorPermission):
    pass


# Email
class EmailViewPolicy(IsOwnerOrReadOnlyPermission):
    pass


class EmailPreferencePolicy(IsOwnerOrReadOnlyPermission):
    pass


# Membership
class MembershipViewPolicy(IsOwnerOrReadOnlyPermission):
    pass


class MembershipPreferencePolicy(IsOwnerOrReadOnlyPermission):
    pass


# Lists
class ListViewPolicy(IsAdminOrReadOnly):
    pass


class ListMembersPolicy(IsAuthenticatedOrReadOnly):
    pass


class ListModeratorsPolicy(IsOwnerOrModeratorPermission):
    pass


class ListOwnerPolicy(IsOwnerOrReadOnlyPermission):
    pass


class ListSettingsPolicy(IsOwnerOrModeratorPermission):
    pass


# Domain
class DomainViewPolicy(IsAdminOrReadOnly):
    pass
