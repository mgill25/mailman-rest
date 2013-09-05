TODO
====

1. As far as models are concerned, have to figure out what specific operations `MM-Core`
   allows us to do. Creating `domain` is allowed, but updating it isn't.
   Creating/Updating an `address` is not allowed.

2. Uniform interface for *secondary* Core entities. List Settings are models on
   their own, but are exposed via `lists/foo@bar.com/config` API etc.

3. Iterating over fields in an adaptor while creating images (in the process of
   pulling things up) -- inside `filter`.

4. Views of `Memberships` filtered by `List` and `Role`. Consider writing
   separate serializers `ListOwnerSerializer`, `ListModeratorSerializer`, and
   `ListSubscriberSerializer` for that.

5. `Preferences` for Users, Emails, Memberships etc. don't need to be "backed up"
   for the first time, since they are at their default values at both levels
   anyway.

6. Make API lookup generic. A `pk` that, if changes, will also affect lookups
   in the related models. See: `ListSettingsViewSet.get_object`.
