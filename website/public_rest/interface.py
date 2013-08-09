#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Layered API Interface.
A model can be "locally" or "remotely" backed up.
"""

import logging
import json
from urlparse import urljoin, urlsplit
from urllib import urlencode

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet, EmptyQuerySet
from model_utils.managers import PassThroughManager

from api import CoreInterface, Connection

LayerBelow = { 'rest': 'core' }


# Abstract Object
class AbstractObject(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def get_logger(cls):
        return logging.getLogger(cls.layer)

    @classmethod
    def get_lower_layer(cls):
        return LayerBelow[cls.layer]

    #@classmethod
    #def get_model(cls):
    #    return models.loading.get_model(__file__.split('/')[-2], '{layer}{object_type}'.format(layer=cls.layer, object_type=cls.object_type))

    #@classmethod
    #def get_backing_model(cls):
    #    return models.loading.get_model(__file__.split('/')[-2], '{layer}{object_type}'.format(layer=cls.get_lower_layer(), object_type=cls.object_type))

    def process_on_save_signal(self, sender, **kwargs):
        instance = kwargs['instance']
        self.get_logger().debug('{object_type}({instance}) has been saved in the {layer} layer'.format(layer=self.layer, object_type=self.object_type, instance=instance.pk))

    def __unicode__(self):
        return '{0}\({1}\)'.format('Class', self.pk)


# QuerySets
class LayeredModelQuerySet(QuerySet):

    def get_logger(self):
        return logging.getLogger(self.model.layer)

    def all(self):
        return self.model.objects.filter()


class LocalObjectQuerySet(LayeredModelQuerySet):
    def filter(self, *args, **kwargs):
        pass


class RemoteObjectQuerySet(LayeredModelQuerySet):
    def filter(self, *args, **kwargs):
        pass


#  Managers
class BaseQueryManager(PassThroughManager):
    def all(self):
        return self.get_query_set().all()

class RemoteManager(BaseQueryManager):
    def get_query_set(self):
        return RemoteObjectQuerySet(self.model)

class LocalManager(BaseQueryManager):
    def get_query_set(self):
        return LocalObjectQuerySet(self.model)


# Abstract Models
class AbstractLocallyBackedObject(AbstractObject):
    class Meta:
        abstract = True

    objects = LocalManager()

    def save(self, *args, **kwargs):
        # Ensure that local object is always related to layer below
        # Stuff
        super(AbstractLocallyBackedObject, self).save(*args, **kwargs)

    def process_on_save_signal(self, sender, **kwargs):
        # Stuff
        super(AbstractLocallyBackedObject, self).process_on_save_signal(sender, **kwargs)

    def delete(self, using=None):
        # delete stuff
        super(AbstractLocallyBackedObject, self).delete(using=using)


class AbstractNopLocalBackup(AbstractObject):
    """
    A local backup which does nothing.
    """
    class Meta:
        abstract = True
    objects = LocalManager()


class AbstractRemotelyBackedObject(AbstractObject):
    partial_URL = models.CharField(max_length=100)

    class Meta:
        abstract = True

    objects = RemoteManager()

    def delete(self, using=None):
        # Stuff
        super(AbstractRemotelyBackedObject, self).delete(using=using)

    def process_on_save_signal(self, sender, **kwargs):
        def get_object(instance, url=None, layer=None):
            """
            Get an object from the remote url if you can.
            This Get works via the CoreInterface objects, and if
            successful, returns the object adaptor.
            """
            pass

        def get_or_create_object(instance, data=None, layer=None):
            """
            The Create works in a similar way. If not present, create
            an object at Remote layer and return the adaptor.
            """
            pass

        # Handle post_save
        # Stuff
        super(AbstractRemotelyBackedObject, self).process_on_save_signal(sender, **kwargs)

