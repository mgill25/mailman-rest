Notes - Ignore
==============

This doc is just observations while reading/writing the code.

A simple object save:

Domain
------
d = Domain()                            # layer_below is `DomainAdaptor`.
d.save()
    -> da = DomainAdaptor()             # What is the layer_below here?
        in `post_save`:
            -> obj = get_or_create()          # via HTTP
            -> save with `partial_URL`

Domain and DomainAdaptor   
------------------------
"If we make the adaptor a regular object and keep primary object as Remotely Backed up."

Domain(AbstractRemotelyBackedObject)
    -> `post_save`
        -> get_object()                     # Gets object from remote (MM-Core)
            -> if partial_url, use it.
               else use instance info (below_key, etc) to GET an object
            -> Make DomainAdaptor out of returned info.     # This functionality should be generic. 

        -> get_or_create_object()
            -> if get_object fails, create one at remote.
            -> 201 returns info of the newly created object. Make an adaptor.

        -> regular `post_save` business.


Adaptor Thingies
----------------
    Q: Why does every adaptor need its own "connection" ?
    A: Because an adaptor gets the info via an API call, which is made by a `Connection` object.
       A connection object has a `call` method, which makes the HTTP call and returns the response.
       All the adaptor does is expose separate methods and properties that represend that response as a complete object.

