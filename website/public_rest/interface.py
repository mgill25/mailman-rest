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

from public_rest.utils import call_api

# XXX: This is causing import error.
#from public_rest.api import CoreInterface, Connection
#core_interface = CoreInterface()

LayerBelow = { 'rest':'adaptor',
'adaptor':'core',
'core': None
}

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

    @classmethod
    def get_model(cls):
        return models.loading.get_model(__file__.split('/')[-2], '{layer}{object_type}'.format(layer=cls.layer, object_type=cls.object_type))

    @classmethod
    def get_backing_model(cls):
        return models.loading.get_model(__file__.split('/')[-2], '{object_type}{layer}'.format(layer=cls.get_lower_layer(), object_type=cls.object_type))

    def process_on_save_signal(self, sender, **kwargs):
        instance = kwargs['instance']
        print('{object_type}({instance}) has been saved in the {layer} layer'.format(layer=self.layer, object_type=self.object_type, instance=instance.pk))

    def __unicode__(self):
        return '{0}\({1}\)'.format('Class', self.pk)


# QuerySets
class LayeredModelQuerySet(QuerySet):

    def get_logger(self):
        return logging.getLogger(self.model.layer)

    def all(self):
        return self.model.objects.filter()


class LocalObjectQuerySet(LayeredModelQuerySet):
    pass
    #def filter(self, *args, **kwargs):
    #    pass


class RemoteObjectQuerySet(LayeredModelQuerySet):
    pass
    #def filter(self, *args, **kwargs):
    #    pass


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
        backing_record = self.layer_below
        if backing_record is None:
            lower_model = self.get_backing_model()
            filter_args = {lower_model.keyed_on: getattr(self, lower_model.keyed_on)}
            print('Backing {object_type} to {layer} layer with {filter}'.format(layer=lower_model.layer, object_type=self.object_type, filter=filter_args))
            backing_record, created = self.get_backing_model().objects.get_or_create(**filter_args)
            self.layer_below = backing_record
        print('Saving {object_type}({pk}) in {layer} layer'.format(layer=self.layer, object_type=self.object_type, pk=self.pk))
        super(AbstractLocallyBackedObject, self).save(*args, **kwargs)

    def process_on_save_signal(self, sender, **kwargs):
        print("Inside AbstractLocallyBackedObject")
        instance = kwargs['instance']
        print('Post_save {object_type} in {layer} layer'.format(layer=self.layer, object_type=self.object_type))
        backing_record = self.layer_below
        print('===Backup is to {layer}{object_type}({0})'.format(backing_record, layer=backing_record.layer, object_type=backing_record.object_type))
        if backing_record:
            for field_name in self.fields:
                field_val = getattr(self, field_name)
                if isinstance(field_val, AbstractObject):
                   print("+  {0}: {1}".format(field_name, field_val))
                   ## Convert field_val to a model
                   below_model = field_val.__class__.get_backing_model()
                   print("        Converting to {0}".format(below_model))
                   field_key = below_model.keyed_on
                   kwds = { field_key : getattr(field_val, field_key) }
                   print("        Creating {0} from {1}".format(field_name, kwds))
                   related_record = below_model.objects.get(**kwds)
                   field_val = related_record
                print("   {0}: {1}".format(field_name, field_val))
                setattr(backing_record, field_name, field_val)
            backing_record.save()
        super(AbstractLocallyBackedObject, self).process_on_save_signal(sender, **kwargs)


        super(AbstractLocallyBackedObject, self).process_on_save_signal(sender, **kwargs)

    #def delete(self, using=None):
    #    # delete stuff
    #    super(AbstractLocallyBackedObject, self).delete(using=using)


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

    def process_on_save_signal(self, sender, **kwargs):
        print("Inside AbstractRemotelyBackedObject!")

        ci = CoreInterface()

        def get_object(instance, url=None, layer=None):
            """
            Returns the ObjectAdaptor.
            """
            if url is None:
                if instance.partial_URL:
                    # We already have a partial url in the database.
                    rv_adaptor = ci.get_object_from_url(partial_url=instance.partial_URL, model=instance.model)
                else:
                    field_key = instance.below_key
                    kwds = { field_key : getattr(instance, field_key) }
                    rv_adaptor = ci.get_object(model=instance.model, object_type=self.object_type, **kwds)
                return rv_adaptor

        def get_or_create_object(instance, data=None, layer=None):
            res = get_object(instance, layer=layer)
            if not res:
                # Push the object on the backer via the REST API.
                rv_adaptor = ci.create_object(object_type=self.object_type, data=data)
                return rv_adaptor
            else:
                return res

        # Handle post_save
        instance = kwargs['instance']
        print('Post_save {object_type} in {layer} layer'.format(layer=self.layer, object_type=self.object_type))
        backing_layer = 'core'
        backing_data = {}
        instance_fields = [fn for fn in instance._meta.get_all_field_names() if fn != u'id']
        for field_name in instance_fields:
            field_val = getattr(instance, field_name)
            if isinstance(field_val, AbstractRemotelyBackedObject):
                if field_val.partial_URL:
                    related_url = urljoin(settings.API_BASE_URL, field_val.partial_URL)
                else:
                    raise Exception('Related Object not Available')
                field_val = related_url
            backing_data[field_name] = field_val
        if kwargs.get('created'):
            res = get_or_create_object(instance, data=backing_data, layer=backing_layer)
            if res:
                # Create a peer thing and associate the url with it.
                instance.partial_URL = urlsplit(res.url).path
                instance.save()
                # Update the information at the back with new data
                ci.update_object(partial_url=instance.partial_URL, data=backing_data)
        else:
            # PATCH the fields in back.
            ci.update_object(partial_url=instance.partial_URL, data=backing_data)
        super(AbstractRemotelyBackedObject, self).process_on_save_signal(sender, **kwargs)

