TODO
====

1. As far as models are concerned, have to figure out what specific operations `MM-Core`
   allows us to do. Creating `domain` is allowed, but updating it isn't.
   Creating/Updating an `address` is not allowed.
            - Current workaround for PATCH - `disallow_updates` list to filter things out.

2. [DONE] `Preferences` for Users, Emails, Memberships etc. don't need to be "backed up"
   for the first time, since they are at their default values at both levels
   anyway.
        Related issue:
            - If something is not backed up, "updating" will have to look
              things up in another way, since we won't have a partial_url.

3. Make API lookup generic. A `pk` that, if changes, will also affect lookups
   in the related models. See: `ListSettingsViewSet.get_object`.

4. DRF - Pagination for secndary endpoint responses, either from the `@action` decorator
   or manually hooked up to the URLConf.

5. DRF - Status Codes should be returned via rest_framework.status, not direct
   ints.

-----
1. `partial_URL` and `path` issues during the connection time.

2. Resources should only have ONE representation -- `foo@bar.com` and
   `foo.bar.com` refer to the same mailing list in Core.

3. Core giving errors during list creation.

4. Proper formatting of data (use endpoints and not queryparams) in filter's
   `sanitize_query_and_endpoint`
