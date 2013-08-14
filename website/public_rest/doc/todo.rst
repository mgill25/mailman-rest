TODO
====

1. As far as models are concerned, have to figure out what specific operations `MM-Core`
   allows us to do. Creating `domain` is allowed, but updating it isn't.
   Creating/Updating an `address` is not allowed.

2. Uniform interface for *secondary* Core entities. List Settings are models on
   their own, but are exposed via `lists/foo@bar.com/config` API etc.

3. Iterating over fields in an adaptor while creating images (in the process of
   pulling things up) -- inside `filter`.
