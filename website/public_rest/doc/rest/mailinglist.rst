============
Mailing List
============

The API exposes a paginated collection of Mailing List, each with its own 
set of settings, some of which can be updated, while others can't. 

You can create a new list, update a list (or a list setting), and remove a list.


        1. Get a collection of lists:
                `GET` on `/api/lists/`

                Successful response:
                    200 OK: *Paginated collection of lists*

                    Response body:
                        <response_body_here>

                Error responses:
                        <error_responses_here>

        2. Create a new list:
                `POST` on `/api/lists/`

                Expected request body:
                    {
                        "display_name" : "MyList",
                        "list_name" : "MyList",
                        "mail_host" : "mail.example.com",
                    }

                Successful response:
                    201 Created: *Created a new mailing list on the domain*

                    Response body:
                        <response_body_here>
