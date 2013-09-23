==========
API Design
==========

Abstract
--------

This application tries to address the problems/lack of features in the Mailman Core API,
which include a better way to represet Users, a way to handle authentication/authorization
in the API, extensible entities in the system. We use Django models which can act independently 
without any connection to the Core, and use DRF to expose them. We also take care of syncing those
models with their corresponding entities at the Core database.


High-Level View
---------------

Each model of the Django REST app correspond to the entities that are present, 
and are exposed by the Mailman Core REST API. They might not be *exact* mirrors,
as they have left out and added some elements, but they represent those same objects,
which are "Resources" for the API.

While a connection to the Core API is required by the app, the idea is
that many of the basic functionalities can be simulated without it, and synced at a later time.

Example:
Lets say you want to register a new User using the API. We don't want that operation to fail
if there was no connection available to the MM-Core. So, we design the system to *cache* the
User's information in the local public_rest database, which can then be synchronised with 
the MM-Core database if need be.

Design Choices
--------------

The API design tries to address the following points:

        * The API needs to be able to represent a distributed authority.  No one component knows, or can be 
          presumed to be authoratative for every entity in the system.
        
        * The API needs to handle per-user authorization, presenting different capabilities to various users.

        * The API needs to present the enterprise from the perspective of the user. 
          In particular, if this "user" is a message handler, it would want to see subscriptions 
          that apply to the current list. But if the user is a subscriber, it wants to see the 
          subscriptions that belong to the subscriber,  In other words, different views of a 
          multi-dimensional array depending on the reason for the access.

        * The representations need to be extensible without requiring every module to support 
          information that it does not need to handle.

        * Thee interface needs to follow the REST design aspects of cacheable and omnipotent operations
        
        * Each component should be able to operate (perhaps with reduced capability) in the absence 
          of a connection to other components.

Elements of the API
-------------------

The REST API has various elements, which we discuss here:

        * **Models**: Each *first class* [1]_ entity in the Mailman system is represented 
          by a Model using the Django ORM. When an instance of the model is created (a new 
          row in the database table), it will only require the minimum amount of information 
          possible, and will add as many defaults as possible. These defaults are the same as the ones
          in the MM-Core entities.
                
        * **Core Interface**: In addition to being able to act as stand-alone objects, the 
          models will also need to be able to communicate with the Mailman Core, and sync 
          any changes they might have. This job is done via an interface to the Core,
          which uses the Internal Core API to interact with the database. Any information 
          that we get from the core interface is wrapped up in proxy objects, which are called *Peer* objects.

        * **DRF**: The Django REST Framework [2]_ is used to actually expose the models. 
          It is a mature, highly extensible framework providing features like browserable API, 
          drop-in extensions to easily expose ORM models as Resources, automatic URL routing, 
          and can be easily extended to expose non-ORM sources as well. 
          We can also hook up authentication easily using DRF. It has excellent documentation, and an active community.

         
.. [1] A first class entity is one that is directly accessible from a URL 
       in the top-level of the API. Second class attributes would be the 
       ones that can be accessed only as a subset of their parents.

.. [2] http://django-rest-framework.org for more details.
