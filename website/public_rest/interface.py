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
from django.core.exceptions import FieldError
from django.db import models
from django.db.models.query import QuerySet, EmptyQuerySet
from model_utils.managers import PassThroughManager

from public_rest.api import CoreInterface, Connection, MailmanConnectionError
from public_rest.utils import get_related_attribute

ci = CoreInterface()

LayerBelow = { 'rest':'adaptor',
'adaptor':'core',
'core': None
}

# Logging
logger = logging.getLogger(__name__)

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
        logger.info('{object_type}({instance}) has been saved in the {layer} layer'.format(layer=self.layer, object_type=self.object_type, instance=instance.pk))

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
        #logger.info("Processing {0} Remote filter!".format(self.model.layer))
        #logger.info("Kwargs: {0}".format(kwargs))

        def sanitize_query_and_endpoint(object_type, endpoint, **kwargs):
            """
            Sanitize query parameters and endpoints for subsequent requests.

            Some arguments come in as kwargs, but need to be propagated below
            as endpoints.

            `kwargs`: All the incoming query parameters.
            `endpoint`: The API endpoint (which may be modified).
            """
            new_dict = {}
            for key, val in kwargs.items():
                if "__exact" in key:
                    key = key.split("__")[0]
                elif  "__" in key:
                    key = key.split("__")[1]
                new_dict[key] = val
            params = urlencode(new_dict)
            return params, endpoint

        # Look at this layer, if empty, look to layers below.
        records = super(RemoteObjectQuerySet, self).filter(*args, **kwargs)
        if records and records.exists():
            return records
        #XXX: filter returns immediately, but DRF makes another call where the condition
        #is false, even when it was true before.
        else:
            #logger.info("Pull records up from {layer} layer".format(layer=self.model.get_lower_layer()))
            endpoint = ci.get_api_endpoint(object_type=self.model.object_type)
            params, endpoint = sanitize_query_and_endpoint(object_type=self.model.object_type,
                                                           endpoint=endpoint, **kwargs)
            lower_url = urljoin('{0}/3.0/'.format(settings.MAILMAN_API_URL),
                                '{0}'.format(endpoint))

            if params:
                #logger.debug("Sanitized Params: {0}".format(params))
                url = urljoin(lower_url, '?{params}'.format(params=params))
            else:
                url = lower_url

            adaptor_list = ci.get_all_from_url(url, object_type=self.model.object_type)

            if len(adaptor_list) == 0:
                return EmptyQuerySet(model=self.model)
            elif len(adaptor_list) > 0:
                # Create the image records and save them on this level
                for record in adaptor_list:
                    logger.debug("Working on {0} record!".format(record))
                    m = self.model()
                    m.partial_URL = urlsplit(record.url).path
                    logger.debug("----------------->>>>")
                    for field in record:
                        if not field in self.FILTER_IGNORE_FIELDS:
                            field_val = getattr(record, field)
                            logger.debug("record field: {0} --- {1}".format(field, field_val))
                            try:
                                setattr(m, field, field_val)
                            except ValueError:
                                # the field is possibly a ForeignKey
                                related_model = getattr(self.model, field).field.rel.to.objects.model
                                logger.info("====Related Model: {0}====".format(related_model))

                                try:
                                    partial_URL = urlsplit(field_val).path
                                except AttributeError:
                                    partial_URL = urlsplit(field_val.url).path

                                try:
                                    related_record = related_model.objects.get(partial_URL=partial_URL)
                                except related_model.DoesNotExist:
                                    raise ValueError("Related record does not exist!")
                                except FieldError:
                                    raise ValueError("partial_URL doesn't exist, the field is not remotely backed up.")
                                except:
                                    logger.debug("+  Exception raised")
                                    raise

                                kwds = { field : getattr(field_val, field) }
                                logger.debug("\tCreating {0} from {1}".format(field, kwds))
                                logger.debug("\tConverting {0}".format(getattr(self.model, field).field.rel.to.objects))
                                related_record = getattr(self.model, field).field.rel.to.objects.get(**kwds)
                                related_record.save()
                                setattr(m, field, related_record)
                                field_val = related_record
                    logger.debug("About to save record m: {0}".format(m))
                    m.save()
                return super(RemoteObjectQuerySet, self).filter(*args, **kwargs)
            else:
                return EmptyQuerySet(model=self.model)


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
        logger.info("Inside AbstractLocallyBackedObject save()")
        #Ensure that local object is always related to layer below
        lower_model = self.get_backing_model()
        logger.info("lower_model: {0}".format(lower_model))
        # Get the arguments associated with our model that might be available at back.
        filter_args = {self.lookup_field: getattr(self, self.lookup_field)}
        logger.info('Backing {object_type} with {filter}'.format(object_type=self.object_type, filter=filter_args))
        backing_record = lower_model.objects.get_or_create(**filter_args)
        #self.layer_below = backing_record
        #logger.info('Saving {object_type}({pk}) in {layer} layer'.format(layer=self.layer, object_type=self.object_type, pk=self.pk))
        super(AbstractLocallyBackedObject, self).save(*args, **kwargs)

    def process_on_save_signal(self, sender, **kwargs):
        logger.info("Inside AbstractLocallyBackedObject post_save()")
        instance = kwargs['instance']
        logger.info('Post_save {object_type}'.format(object_type=self.object_type))
        lookup_args = {self.lookup_field: getattr(self, self.lookup_field)}
        logger.info("lookup_args: {0}".format(lookup_args))
        backing_record = self.get_backing_model().objects.get(**lookup_args)
        logger.info('===Backup is to {object_type}({0})'.format(backing_record, object_type=backing_record.object_type))
        if backing_record:
            for local_field_name, remote_field_name in self.fields:
                field_val = get_related_attribute(self, local_field_name)
                if isinstance(field_val, AbstractObject):
                   #logger.debug("+  {0}: {1}".format(local_field_name, field_val))
                   ## Convert field_val to a model
                   #logger.debug("        Converting to {0}".format(below_model))
                   field_key = self.lookup_field
                   kwds = { field_key : getattr(field_val, field_key) }
                   #logger.debug("        Creating {0} from {1}".format(local_field_name, kwds))
                   related_record = below_model.objects.get(**kwds)
                   field_val = related_record
                logger.info("   {0}: {1}".format(local_field_name, field_val))
                setattr(backing_record, local_field_name, field_val)
            backing_record.save()
        super(AbstractLocallyBackedObject, self).process_on_save_signal(sender, **kwargs)

    def delete(self, using=None):
        # First delete locally
        #obj_below = self.layer_below
        super(AbstractLocallyBackedObject, self).delete(using=using)
        # Now delete remotely
        #obj_below.delete()

    def delete_local(self, using=None):
        """Only perform local delete"""
        return super(AbstractLocallyBackedObject, self).delete(using=using)


class AbstractRemotelyBackedObject(AbstractObject):
    partial_URL = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True

    objects = RemoteManager()

    def process_on_save_signal(self, sender, **kwargs):
        """
        After saving the object locally, we sync the
        changes to the remotely backed layer as well.
        """
        logger.info("Inside AbstractRemotelyBackedObject!")

        # TODO: Properly handle disallowed methods for objects
        disallow_updates = ['domain', 'mailinglist', 'membership',
                            'preferences']   # You can PATCH `deliver_mode` on membership preferences.

        def prepare_related_data(instance):
            """Prepare data that would be used for looking
            up objects remotely."""
            data = {}
            if self.object_type == 'membership':
                data['list_id'] = self.mlist.fqdn_listname
            if self.object_type == 'listsettings':
                data['fqdn_listname'] = self.fqdn_listname
            if self.object_type == 'preferences':
                data['address'] = self.membership.address.address
                data['list_id'] = self.membership.fqdn_listname
            if self.object_type == 'user':
                data['email'] = self.preferred_email.address
            return data

        def prepare_backing_data(instance):
            """Prepare data for backing layer"""
            # Local fields could have different name at remote
            backing_data = {}
            for local_field_name, remote_field_name in instance.fields:
                field_val = get_related_attribute(instance, local_field_name)
                if isinstance(field_val, AbstractRemotelyBackedObject):
                    if field_val.partial_URL:
                        related_url = urljoin(settings.API_BASE_URL, field_val.partial_URL)
                    else:
                        raise Exception('Related Object not Available')
                    field_val = related_url
                backing_data[remote_field_name] = field_val
            return backing_data

        def get_object(instance):
            """Returns the ObjectAdaptor. """
            object_model = instance.__class__
            field_key = getattr(instance, 'lookup_field', None)
            if not field_key:
                kwds = {}
            else:
                kwds = { field_key : getattr(instance, field_key, None) }
            kwds.update(prepare_related_data(instance))
            try:
                adaptor = ci.get_object(partial_url=instance.partial_URL, object_type=self.object_type, **kwds)
            except HTTPError:
                return None
            return adaptor

        def get_or_create_object(instance, data=None):
            object_model = instance.__class__
            res = get_object(instance)
            if not res:
                # Push the object on the backer via the REST API.
                logger.debug("GET failed!")
                logger.debug("Creating object...")
                kwds = prepare_related_data(instance)
                rv_adaptor = ci.create_object(object_type=self.object_type, data=data, **kwds)
                return rv_adaptor
            else:
                return res

        def backup_object(instance):
            logger.debug("data: {0}".format(backing_data))
            res = get_or_create_object(instance, data=backing_data)
            if res:
                logger.debug("result: {0}, {1}".format(res, type(res)))
                # Create a peer thing and associate the url with it.
                instance.partial_URL = urlsplit(res.url).path
                instance.save()
                # Update the information at the back with new data.
                # >> Depends on the object_type
            else:
                if instance.object_type not in disallow_updates:
                    ci.update_object(object_type=self.object_type,
                            partial_url=instance.partial_URL, data=backing_data)

        # Handle post_save
        logger.info('Post_save {object_type} in {layer} layer'.format(
            layer=self.layer, object_type=self.object_type))

        instance = kwargs['instance']
        backing_data = prepare_backing_data(instance)
        # handle object get/create
        try:
            if kwargs.get('created'):
                backup_object(instance)
            else:
                # PATCH the fields in back.
                if instance.partial_URL:
                    if instance.object_type not in disallow_updates:
                        logger.debug("partial_url: {0}".format(instance.partial_URL))
                        ci.update_object(object_type=self.object_type,
                                         partial_url=instance.partial_URL,
                                         data=backing_data)
                else:
                    # No partial URL, object is to be completely backed up
                    backup_object(instance)
            super(AbstractRemotelyBackedObject, self).process_on_save_signal(sender, **kwargs)
        except MailmanConnectionError as e:
            logger.info("Could not back up properly: {0}".format(e))
