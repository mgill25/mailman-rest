======
Domain
======


Domain Collection
-----------------

$ curl http://localhost:8000/api/domains/ -u admin:password

{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "url": "http://localhost:8000/api/domains/1/",
            "base_url": "foobuzz.com",
            "mail_host": "mail.foobuzz.com"
        },
        {
            "url": "http://localhost:8000/api/domains/2/",
            "base_url": "example.com",
            "mail_host": "mail.example.com"
        }

    ]
}

Get an individual Domain
------------------------

Follow the url in the collection results to get the information about an individual domain.

$ curl http://localhost:8000/api/domains/1/ -u admin:password

{
    "url": "http://localhost:8000/api/domains/1/",
    "base_url": "foobuzz.com",
    "mail_host": "mail.foobuzz.com",
    "contact_address": "",
    "description": "",
    "mailinglist_set": [
        {
            "url": "http://localhost:8000/api/lists/1/",
            "fqdn_listname": "test1@mail.foobuzz.com"
        },
        {
            "url": "http://localhost:8000/api/lists/2/",
            "fqdn_listname": "test2@mail.foobuzz.com"
        },
        {
            "url": "http://localhost:8000/api/lists/3/",
            "fqdn_listname": "newlist@mail.foobuzz.com"
        }
    ]
}

Creating a new Domain
---------------------

We can create a new Domain by POSTing to the ``/domains`` endpoint.
Only parameter needed is ``mail_host``. ``base_url`` is provided by default if not supplied.

$ curl -X POST http://localhost:8000/api/domains/ --data "mail_host=example2.com" -u admin:password

{
    "url": "http://localhost:8000/api/domains/4/",
    "base_url": "http://example1.com",
    "mail_host": "example1.com"
}


Deleting a Domain
-----------------

Deleting an existing domain is just as easy.

$ curl -i -X DELETE http://localhost:8000/api/domains/5/ -u admin:password

HTTP/1.0 204 NO CONTENT
Date: Mon, 09 Sep 2013 11:57:54 GMT
Server: WSGIServer/0.1 Python/2.7.3
Vary: Accept, Accept-Language, Cookie
Content-Length: 0
Content-Type: application/json
Content-Language: en-us
Allow: GET, PUT, DELETE, HEAD, OPTIONS, PATCH


Updating a Domain
-----------------

You can update the description or contact address on a Domain.
$ curl -i --request PATCH --data "description=New Description!" http://localhost:8000/api/domains/4/ -u admin:password

HTTP/1.0 204 NO CONTENT
Date: Mon, 09 Sep 2013 12:15:50 GMT
Server: WSGIServer/0.1 Python/2.7.3
Vary: Accept, Accept-Language, Cookie
Content-Length: 0
Content-Type: application/json
Content-Language: en-us
Allow: GET, PUT, DELETE, HEAD, OPTIONS, PATCH


The updated details can be seen by doing a GET
$ curl http://localhost:8000/api/domains/4/ -u admin:password

{
    "url": "http://localhost:8000/api/domains/3/",
    "base_url": "http://hellogoodbye.com",
    "mail_host": "hellogoodbye.com",
    "contact_address": "",
    "description": "New Description",
    "mailinglist_set": []
}
