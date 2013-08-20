===========
Preferences
===========

Just like the Core, we have various levels of preferences in the layer.

"System" and "Membership" preferences are read-only and can not be modified.

But preferences of an individual entity (an `address` in `Core`) can be
modified using PUT or PATCH requests (maybe POST also, haven't checked yet).


For a membership object, we can have 3 types of preferences, based on the role
of the subscriber:
::
    >>> mem1 =  Membership(user=u1, mlist=mlist, address='tonystark@mail.localhost')
    >>> mem1.preferences
    <MemberPrefs: MemberPrefs object>

    >>> mem2 =  Membership(user=u2, mlist=mlist, address='tonystark2@mail.localhost')
    >>> mem2.preferences
    <OwnerPrefs: OwnerPrefs object>

    >>> mem3 =  Membership(user=u3, mlist=mlist, address='tonystark3@mail.localhost')
    >>> mem3.preferences
    <ModeratorPrefs: ModeratorPrefs object>
    
A membership only has preferences for its own role. Trying to access other
roles raises `DoesNotExist` exception.
::
    >>> mem1.memberprefs
    <MemberPrefs: MemberPrefs object>
    >>> mem1.ownerprefs
    Traceback (most recent call last)
    ...
    DoesNotExist: 

Hence, the *preferences* attribute should be used to access preferences, and
not individual attributes for members, moderators or owners.

