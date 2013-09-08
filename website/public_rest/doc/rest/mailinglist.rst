============
Mailing List
============

The API exposes a paginated collection of Mailing List, each with its own 
set of settings, some of which can be updated, while others are read-only. 

You can create a new list, update a list (or a list setting), and remove a list.

Getting list collection 
-----------------------

Lists are available as paginated responses.

There are no lists right now.

$ curl http://localhost:8000/api/lists/ -u admin:password

{
    "count": 0, 
    "next": null, 
    "previous": null, 
    "results": []
}
 

After creation of a list

$ curl http://localhost:8000/api/lists/ -u admin:password

{
    "count": 1, 
    "next": null, 
    "previous": null, 
    "results": [
        {
            "url": "http://localhost:8000/api/lists/1/", 
            "fqdn_listname": "test1@mail.foobuzz.com", 
            "list_name": "test1", 
            "mail_host": "mail.foobuzz.com"
        }
    ]
}

Getting a list
--------------

We can follow the url in the List result in order to find more information about the list.
For example, the above response returns one list as a result, which has a url.

$ curl http://localhost:8000/api/lists/1/ -u admin:password
{
    "url": "http://localhost:8000/api/lists/1/", 
    "fqdn_listname": "test1@mail.foobuzz.com", 
    "list_name": "test1", 
    "mail_host": "mail.foobuzz.com", 
    "members": [], 
    "owners": [], 
    "moderators": [], 
    "settings": "http://localhost:8000/api/lists/1/settings/"
}

Filtering
---------

We can also try to find a list by filtering it out using a query parameter
(for example "list_name" or "fqdn_listname").

$ curl http://localhost:8000/api/lists/?list_name=test1 -u admin:password
{
    "url": "http://localhost:8000/api/lists/1/", 
    "fqdn_listname": "test1@mail.foobuzz.com", 
    "list_name": "test1", 
    "mail_host": "mail.foobuzz.com", 
    "members": [], 
    "owners": [], 
    "moderators": [], 
    "settings": "http://localhost:8000/api/lists/1/settings/"
}

Creating a new list
-------------------

Lists can be created by making a POST request to lists collection.
In order to create a list, make sure there is already a Domain that exists. 
The parameters to provide for the creation of lists are `mail_host` and `list_name`.

$ curl --data "mail_host=mail.foobuzz.com&list_name=newlist" http://localhost:8000/api/lists/ -u admin:password
{
    "url": "http://localhost:8000/api/lists/2/", 
    "fqdn_listname": "newlist@mail.foobuzz.com", 
    "list_name": "newlist", 
    "mail_host": "mail.foobuzz.com"
}
    
Deleting a list
---------------

Lets delete the list we just created above

$ curl -i -X DELETE http://localhost:8000/api/lists/2/ -u admin:password

HTTP/1.0 204 NO CONTENT
Date: Sun, 08 Sep 2013 11:40:12 GMT
Server: WSGIServer/0.1 Python/2.7.3
Vary: Accept, Accept-Language, Cookie
Content-Length: 0
Content-Type: application/json
Content-Language: en-us
Allow: GET, PUT, DELETE, HEAD, OPTIONS, PATCH

