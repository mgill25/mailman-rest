=====
Users
=====

The REST API can be used to add and remove users, add and remove user
addresses, and change their preferred address, password, name, etc.

Get User collection
-------------------

$ curl http://localhost:8000/api/users/ -u admin:password
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "url": "http://localhost:8000/api/users/3/",
            "display_name": "Bruce Wayne",
            "is_superuser": false,
            "preferred_email": "http://localhost:8000/api/emails/4/"
        },
        {
            "url": "http://localhost:8000/api/users/4/",
            "display_name": "admin",
            "is_superuser": true,
            "preferred_email": "http://localhost:8000/api/emails/5/"
        }
    ]
}



Get user details
----------------

$ curl http://localhost:8000/api/users/3/ -u admin:password
{
    "url": "http://localhost:8000/api/users/3/",
    "display_name": "Bruce Wayne",
    "is_superuser": false,
    "emails": [
        "bruce@wayne.com"
    ],
    "preferred_email": "http://localhost:8000/api/emails/4/"
    "membership_set": [
        {
            "url": "http://localhost:8000/api/memberships/1/",
            "address": "http://localhost:8000/api/emails/5/"
        }
    ]

}

We can take a look at all the related memberships and email addresses in the
detail view.

User Emails
-----------

A user endpoint also has a related secondary endpoint for emails. We can use
this in order to get the details of all the emails related to a user, and
creation and deletion of emails related to that user.

$ curl http://localhost:8000/api/users/4/emails/ -u admin:password
[
    {
        "url": "http://localhost:8000/api/emails/6/",
        "address": "admin@adminuser.com",
        "user": "admin",
        "verified": false
    }
]

Associating new email
---------------------

We can associate a new email address to a given user by POSTing
to the user's endpoint, with a parameter called `address` that specifies
the email address.

$ curl -X POST --data "address=newemailaddress@yahoo.com" http://localhost:8000/api/users/4/emails/ -u admin:password
{
    "url": "http://localhost:8000/api/emails/6/",
    "address": "newemailaddress@yahoo.com",
    "user": "admin",
    "verified": false
}


Filtering
---------

We can query the API to get a filtered result based on parameters like
display_name or email address.

For example, to get the user with the display_name "admin":
$ curl http://localhost:8000/api/users/?display_name=admin -u admin:password
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "url": "http://localhost:8000/api/users/4/",
            "display_name": "admin",
            "is_superuser": true,
            "preferred_email": "http://localhost:8000/api/emails/5/"
        }
    ]
}

or display the information of a user with the given email address:
$ curl http://localhost:8000/api/users/?email=hello@goodbye.com -u admin:password
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "url": "http://localhost:8000/api/users/2/",
            "display_name": "testuser",
            "is_superuser": true,
            "preferred_email": "http://localhost:8000/api/emails/2/"
        }
    ]
}

