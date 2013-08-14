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
from urllib2 import HTTPError

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet, EmptyQuerySet
from model_utils.managers import PassThroughManager

from public_rest.api import CoreInterface, Connection

ci = CoreInterface()

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

    FILTER_IGNORE_FIELDS = ['url', ]

    def filter(self, *args, **kwargs):
        print("Processing {0} Remote filter!".format(self.model.layer))
        print("Kwargs: {0}".format(kwargs))

        # Look at this layer, if empty, look to layers below.
        records = super(RemoteObjectQuerySet, self).filter(*args, **kwargs)
        if records and records.exists():
            return records
        else:
            print("Pull records up from {layer} layer".format(layer=self.model.get_lower_layer()))
            endpoint = self.model.object_type + 's'
            lower_url = urljoin(settings.MAILMAN_API_URL, '/{endpoint}'.format(endpoint=endpoint))
            # Sanitize query parameters for subsequent requests.
            new_dict = {}
            for key, val in kwargs.items():
                if "__exact" in key:
                    key = key.split("__")[0]
                new_dict[key] = val
            params = urlencode(new_dict)              # Turn all kwargs into Query parameters
            if params:
                url = urljoin(lower_url, '?{params}'.format(params=params))
            else:
                url = lower_url
            adaptor_list = ci.get_all_from_url(url)
            if len(adaptor_list) == 0:
                return EmptyQuerySet()
            elif len(adaptor_list) > 0:
                # Create the image records and save them on this level
                for record in adaptor_list:
                    m = self.model()
                    m.partial_URL = urlsplit(record.url).path
                    #self.get_logger().debug("Saving {1}{0}".format(self.model.object_type, m.layer))
                    #self.get_logger().debug(" {0}".format(record))
                    for field in record():
                        if not field in self.FILTER_IGNORE_FIELDS:
                            self.get_logger().debug("   Field: {0}".format(field))
                            ###  When the field is a ForeignKey URL, we must convert it to the current layer
                            field_val = getattr(record, field)
                            try:
                               setattr(m, field, field_val)
                            except ValueError:
                               #self.get_logger().debug("+  {0}: {1}".format(field, field_val))
                               related_model = getattr(self.model, field).field.rel.to.objects.model
                               partial_URL = urlsplit(field_val).path
                               try:
                                   related_record = related_model.objects.get(partial_URL=partial_URL)
                               except:
                                   self.get_logger().debug("+  Exception raised")
                                   raise

                               #field_key = field_val.keyed_on
                               #kwds = { field_key : getattr(field_val, field_key) }
                               #self.get_logger().debug("        Creating {0} from {1}".format(field, kwds))
                               #self.get_logger().debug("        Converting {0}".format(getattr(self.model, field).field.rel.to.objects))
                               #related_record = getattr(self.model, field).field.rel.to.objects.get(**kwds)
                               #related_record.save()
                               setattr(m, field, related_record)
                               field_val = related_record
                            self.get_logger().debug("   {0}: {1}".format(field, field_val))
                    m.save()
                return super(RemoteObjectQuerySet, self).filter(*args, **kwargs)
            else:
                return EmptyQuerySet()


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
        # Stuff
        super(AbstractLocallyBackedObject, self).save(*args, **kwargs)

    def process_on_save_signal(self, sender, **kwargs):
        # Stuff
        super(AbstractLocallyBackedObject, self).process_on_save_signal(sender, **kwargs)

    def delete(self, using=None):
        # delete stuff
        super(AbstractLocallyBackedObject, self).delete(using=using)


class AbstractRemotelyBackedObject(AbstractObject):
    partial_URL = models.CharField(max_length=100)

    class Meta:
        abstract = True

    objects = RemoteManager()

    def process_on_save_signal(self, sender, **kwargs):
        """
        After saving the object locally, we sync the
        changes to the remotely backed layer as well.
        """
        print("Inside AbstractRemotelyBackedObject!")

        def get_object(instance, url=None):
            """
            Returns the ObjectAdaptor.
            """
            if url is None:
                object_model = instance.__class__
                if instance.partial_URL:
                    # We already have a partial url in the database.
                    rv_adaptor = ci.get_object_from_url(partial_url=instance.partial_URL, object_type=self.object_type)
                else:
                    field_key = instance.lookup_field
                    kwds = { field_key : getattr(instance, field_key) }
                    try:
                        rv_adaptor = ci.get_object(object_type=self.object_type, **kwds)
                    except HTTPError:
                        return None
                return rv_adaptor

        def get_or_create_object(instance, data=None):
            object_model = instance.__class__
            res = get_object(instance)
            if not res:
                # Push the object on the backer via the REST API.
                extra_args = {}
                if self.object_type == 'listsettings':
                    extra_args = { 'fqdn_listname': instance.mailinglist.fqdn_listname }
                rv_adaptor = ci.create_object(object_type=self.object_type, data=data, **extra_args)
                return rv_adaptor
            else:
                return res

        def prepare_backing_data(instance):
            backing_data = {}
            for field_name in instance.fields:
                field_val = getattr(instance, field_name)
                if isinstance(field_val, AbstractRemotelyBackedObject):
                    if field_val.partial_URL:
                        related_url = urljoin(settings.API_BASE_URL, field_val.partial_URL)
                    else:
                        raise Exception('Related Object not Available')
                    field_val = related_url
                backing_data[field_name] = field_val
            return backing_data


        # Handle post_save
        instance = kwargs['instance']
        print('Post_save {object_type} in {layer} layer'.format(layer=self.layer, object_type=self.object_type))

        backing_data = prepare_backing_data(instance)

        # handle object get/create
        # TODO: Properly handle disallowed methods for objects

        disallow_updates = ['domain', ]

        if kwargs.get('created'):
            print("data: ", backing_data)
            res = get_or_create_object(instance, data=backing_data)
            if res:
                # Create a peer thing and associate the url with it.
                instance.partial_URL = urlsplit(res.url).path
                instance.save()
                # Update the information at the back with new data.
                # >> Depends on the object_type
            else:
                if instance.object_type not in disallow_updates:
                    ci.update_object(partial_url=instance.partial_URL, data=backing_data)
        else:
            # PATCH the fields in back.
            if instance.object_type not in disallow_updates:
                ci.update_object(partial_url=instance.partial_URL, data=backing_data)
        super(AbstractRemotelyBackedObject, self).process_on_save_signal(sender, **kwargs)

