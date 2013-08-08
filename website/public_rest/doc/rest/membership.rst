===========
Memberships
===========

Membership objects represent the relationship between a User and a Mailing List.

        1. Create a new membership (Subscribe a User to a Mailing List):
                `POST` to `/api/membership/`

                Expected request body:
                        {
                                "user" : <user_id> or <user_name>,
                                "email": <email_address>,
                                "list" : <list_id> or <fqdn_listname>,
                                "relationship": "member" or "moderator" or "owner"
                        }

                Successful Response: 
                        201: *Created a new membership record. Given email address is now subscribed to the mailing list.*
                         
                        Response body:
                                        <response_body_here> 
                

                Error Responses:
                        <error_responses_here>        


        2. Updating a Membership record:


        3. Deleting a Membership record (Unsubscribing): 
