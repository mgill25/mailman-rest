==========
Operations
==========

The following are possible operations that can be performed on the REST API.


Users
-----
        1. Get all users (paginated).
                   * Get `ALL` users in one requests ?
                   * Get Paginated Users, so we can go through records via `page number` and `count`.

        2. Get *some* users (can be only 1) based on a *filter*. For example:
                   * Display Name
                   * Email
                        * Verified or Not
                   * At least one verified email.
                   * Subscribed to a mailing list.
                   * etc.

        3. Create a new user.

        4. Change a user setting.

        5. Add/Remove a new email address for a user.

        6. Make an email address `preferred` for a user (first one is the default).


Lists
-----
        1. Get all mailing lists on *this* domain.

        2. Get some lists based on a *filter*. For example:
                   * Lists subscribed by X user.
                   * Lists older than D date. 
                   * Lists where the user U is a moderator.
                   * etc.

        3. Create a new mailing list on *this* domain.

        4. Change a list setting (Note that some are not modifiable).


Memberships
-----------

        *A Membership is created when a user is subscribed to a mailing list. Creation is performed
        directly on the Membership endpoint rather than the User or List Endpoint*.

        1. Get all the existing memberships in the system (for *all* lists in the system).

        2. Get all memberships for a given filter (eg: all memberships for a given MailingList).

        3. Create a new membership between a given User (or an Email address) and a MailingList.

        4. Change the delivery address for a given membership a User can have multiple addresses, 
           and can chose to change them for a given mailing list subscription).

        5. Change the membership *role*: (Moderator, Owner or Member).


