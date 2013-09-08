=============
List Settings
=============

Every mailing list has a number of settings which are exposed by
the secondary URL at `/lists/list_id/settings`. If a setting is READ-ONLY,
modifying it would not change anything, but if not, the setting would be
replaced by the new data (if valid).

Say we have an existing list at `/lists/3/`, we can get the settings at
`lists/3/settings/`. Like so:

$ curl http://localhost:8000/api/lists/3/settings/ -u admin:password
{
    "url": "http://localhost:8000/api/lists/3/settings/",
    "admin_immed_notify": true,
    "admin_notify_mchanges": false,
    "archive_policy": "public",
    "administrivia": true,
    "advertised": true,
    "allow_list_posts": true,
    "anonymous_list": false,
    "autorespond_owner": "none",
    "autoresponse_owner_text": "",
    "autorespond_postings": "none",
    "autoresponse_postings_text": "",
    "autorespond_requests": "none",
    "autoresponse_request_text": "",
    "collapse_alternatives": true,
    "convert_html_to_plaintext": false,
    "filter_content": false,
    "first_strip_reply_to": false,
    "include_rfc2369_headers": true,
    "reply_goes_to_list": "no_munging",
    "send_welcome_message": true,
    "display_name": "",
    "autoresponse_grace_period": "90d",
    "bounces_address": "newlist4-bounces@mail.foobuzz.com",
    "default_member_action": "defer",
    "default_nonmember_action": "hold",
    "description": "",
    "digest_size_threshold": 30.0,
    "join_address": "newlist4-join@mail.foobuzz.com",
    "leave_address": "newlist4-leave@mail.foobuzz.com",
    "mail_host": "mail.foobuzz.com",
    "next_digest_number": 1,
    "no_reply_address": "noreply@mail.foobuzz.com",
    "owner_address": "newlist4-owner@mail.foobuzz.com",
    "post_id": 1,
    "posting_address": "",
    "posting_pipeline": "default-posting-pipeline",
    "reply_to_address": "",
    "request_address": "newlist4-request@mail.foobuzz.com",
    "scheme": "",
    "volume": 1,
    "subject_prefix": "",
    "web_host": "",
    "welcome_message_uri": "mailman:///welcome.txt",
    "fqdn_listname": "newlist4@mail.foobuzz.com",
    "last_post_at": null,
    "digest_last_sent_at": null
}


Partially updating settings
---------------------------

Individual settings can be updated via the HTTP `PATCH` request.

$ curl --request PATCH
       --data "autoresponse_owner_text=hellllllo&admin_notify_mchanges=true"
       http://localhost:8000/api/lists/3/settings/ -u admin:password


On the next `GET`, the settings will display the updated values.

$ curl http://localhost:8000/lists/3/settings/ -u admin:password
{
    "url": "http://localhost:8000/api/lists/3/settings/",
    "admin_notify_mchanges": true,
    "autoresponse_owner_text": "hellllllo",
    ...
}

Completely updating settings
----------------------------
Use the `POST` request and specify ALL the settings in order to update them.

