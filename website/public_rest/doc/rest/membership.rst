===========
Memberships
===========

Membership (or Subscriptions) represent the relationship between a User and a Mailing List.

A membership is unique cross-product over the ``{mailinglist, role, address}`` set.

Membership Collection
---------------------

You can view the list of all memberships for a given mailing list on the
``/lists/<list_id>/memberships/`` endpoint. This will return the entire roster
for that list - members, owners and moderators.

$ curl http://localhost:8000/api/lists/1/memberships/ -u admin:password
[
    {
        "address": "http://localhost:8000/api/emails/5/",
        "role": "member",
        "user": "http://localhost:8000/api/users/1/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/7/",
        "role": "member",
        "user": "http://localhost:8000/api/users/2/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/8/",
        "role": "member",
        "user": "http://localhost:8000/api/users/3/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/9/",
        "role": "member",
        "user": "http://localhost:8000/api/users/4/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/10/",
        "role": "moderator",
        "user": "http://localhost:8000/api/users/5/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/12/",
        "role": "owner",
        "user": "http://localhost:8000/api/users/6/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/13/",
        "role": "owner",
        "user": "http://localhost:8000/api/users/7/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/14/",
        "role": "owner",
        "user": "http://localhost:8000/api/users/8/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/15/",
        "role": "owner",
        "user": "http://localhost:8000/api/users/9/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
    {
        "address": "http://localhost:8000/api/emails/5/",
        "role": "owner",
        "user": "http://localhost:8000/api/users/10/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/2/",
            "fqdn_listname": "fedex_list@mail.example.com"
        }
    }
]


Membership Filtering
--------------------

Members can also be filtered based on their role.
Example, for all the moderators on the list...

$ curl http://localhost:8000/api/lists/1/moderators/ -u admin:password
[
    {
        "address": "http://localhost:8000/api/emails/10/",
        "role": "moderator",
        "user": "http://localhost:8000/api/users/5/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    }
]

...and similary, for all the owners of the list

$ curl http://localhost:8000/api/lists/1/owners/ -u admin:password
[
    {
        "address": "http://localhost:8000/api/emails/12/",
        "role": "owner",
        "user": "http://localhost:8000/api/users/6/",
        "mlist": {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        }
    },
]

Similary, we have ``api/lists/<list_id>/members/`` to query all the members for
the mailing list!

Getting Individual Subscriptions
--------------------------------

Individual subscriptions can be accessed via ``api/lists/<list_id>/members/<email_address>``
endpoint.

$ curl -i http://localhost:8000/api/lists/1/members/foo@bar.com/ -u admin:password
HTTP/1.0 200 OK
Date: Fri, 13 Sep 2013 12:28:43 GMT
Server: WSGIServer/0.1 Python/2.7.3
Vary: Accept, Accept-Language, Cookie
Content-Type: application/json
Content-Language: en-us
Allow: GET, POST, PUT, DELETE, HEAD, OPTIONS, PATCH

{
    "address": "http://localhost:8000/api/emails/2/",
    "role": "member",
    "user": "http://localhost:8000/api/users/3/",
    "mlist": {
        "url": "http://localhost:8000/api/lists/1/",
        "fqdn_listname": "newlist@hellogoodbye.com"
    }
}


Subscribing to Lists (Creating new memberships)
-----------------------------------------------

The above endpoints for members, moderators, and owners can be used to create
new subscriptions. POST request to these urls, along with an ``address`` parameter which
should have the email address of the desired subscription can be used to create new memberships.

Lets create a new member on the mailinglist with id 1:

$ curl -i -X POST --data "address=my_address@gmail.com" http://localhost:8000/api/lists/1/members/ -u admin:password
HTTP/1.0 201 CREATED
Date: Wed, 11 Sep 2013 15:13:26 GMT
Server: WSGIServer/0.1 Python/2.7.3
Vary: Accept, Accept-Language, Cookie
Content-Type: application/json
Content-Language: en-us
Allow: GET, POST, HEAD, OPTIONS

{
    "address": "http://localhost:8000/api/emails/17/",
    "role": "member",
    "user": "http://localhost:8000/api/users/14/",
    "mlist": {
        "url": "http://localhost:8000/api/lists/1/",
        "fqdn_listname": "test2@mail.foobuzz.com"
    }
}

We can also subscribe to lists using a ``User``.

 - If we provide only a user's display_name, her preferred email address is used for subscription.

 - If we provide an address as well, it is first checked to be associated with the User,
   and only then subscribed.

 - If we do not provide any address or display_name, the subscription is created with the logged-in
   user's preferred address.


Unsubscribe from Lists
----------------------

Unsubscription means deleting an existing membership. A `DELETE` on the
membership's URL leads to the unsubscription!

$ curl -i -X DELETE http://localhost:8000/api/lists/1/members/foo@bar.com/ -u admin:password
HTTP/1.0 204 NO CONTENT
Date: Fri, 13 Sep 2013 12:32:20 GMT
Server: WSGIServer/0.1 Python/2.7.3
Vary: Accept, Accept-Language, Cookie
Content-Length: 0
Content-Type: application/json
Content-Language: en-us
Allow: GET, POST, PUT, DELETE, HEAD, OPTIONS, PATCH


