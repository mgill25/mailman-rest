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
        logger.info("Processing {0} Remote filter!".format(self.model.layer))
        logger.info("Kwargs: {0}".format(kwargs))

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
            logger.info("Pull records up from {layer} layer".format(layer=self.model.get_lower_layer()))
            try:
                endpoint = ci.get_api_endpoint(object_type=self.model.object_type)
            except ValueError:
                adaptor_list = []
            else:
                params, endpoint = sanitize_query_and_endpoint(object_type=self.model.object_type,
                                                               endpoint=endpoint, **kwargs)
                lower_url = urljoin('{0}/3.0/'.format(settings.MAILMAN_API_URL),
                                    '{0}'.format(endpoint))
                if params:
                    url = urljoin(lower_url, '?{params}'.format(params=params))
                else:
                    url = lower_url
                try:
                    adaptor_list = ci.get_all_from_url(url, object_type=self.model.object_type)
                except MailmanConnectionError as e:
                    logger.info("Exception - {0}".format(e))
                    adaptor_list = []

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
                            logger.debug("field: {0}, {1}".format(field, type(field)))
                            logger.debug("field_val: {0}, {1}".format(field_val, type(field_val)))
                            try:
                                setattr(m, field, field_val)
                            except ValueError:
                                related_model = getattr(self.model, field).field.rel.to.objects.model
                                logger.info("====Related Model: {0}====".format(related_model))
                                try:
                                    related_record = ci.create_model_from_adaptor(related_model, field_val)
                                    setattr(m, field, related_record)
                                except Exception as e:
                                    logger.debug("===Exception=== {0}".format(e))
                    m.save()
                    logger.debug("Saved record m: {0}".format(m))
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

    # TODO: Properly handle disallowed methods for objects
    disallow_updates = ['domain',
                        'mailinglist',
                        'membership',
                        'preferences']   # You can PATCH `deliver_mode` on membership preferences.

    class Meta:
        abstract = True

    objects = RemoteManager()

    def prepare_related_data(self):
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

    def prepare_backing_data(self):
        """Prepare data for backing layer"""
        # Local fields could have different name at remote
        backing_data = {}
        for local_field_name, remote_field_name in self.fields:
            field_val = get_related_attribute(self, local_field_name)
            if isinstance(field_val, AbstractRemotelyBackedObject):
                if field_val.partial_URL:
                    related_url = urljoin(settings.MAILMAN_API_URL, field_val.partial_URL)
                    field_val = related_url
            backing_data[remote_field_name] = field_val
        return backing_data

    def get_object(self):
        """Returns the ObjectAdaptor. """
        object_model = self.__class__
        field_key = getattr(self, 'lookup_field', None)
        if not field_key:
            kwds = {}
        else:
            kwds = { field_key : getattr(self, field_key, None) }
        kwds.update(self.prepare_related_data())
        try:
            adaptor = ci.get_object(partial_url=self.partial_URL, object_type=self.object_type, **kwds)
        except HTTPError as e:
            logger.info("Could not GET object: {0}".format(e))
            return None
        return adaptor

    def get_or_create_object(self, data=None):
        object_model = self.__class__
        res = self.get_object()
        if not res:
            # Push the object on the backer via the REST API.
            logger.debug("GET failed!")
            logger.debug("Creating object...")
            kwds = self.prepare_related_data()
            try:
                rv_adaptor = ci.create_object(object_type=self.object_type, data=data, **kwds)
            except HTTPError as e:
                logger.info("Could not CREATE object - {0}".format(e))
                return None
            else:
                return rv_adaptor
        else:
            return res

    def create_backup(self, backing_data):
        logger.debug("data: {0}".format(backing_data))
        res = self.get_or_create_object(data=backing_data)
        if res:
            logger.debug("result: {0}, {1}".format(res, type(res)))
            # Create a peer thing and associate the url with it.
            self.partial_URL = urlsplit(res.url).path
            self.save()
            # Update the information at the back with new data.
            # >> Depends on the object_type
        else:
            if self.object_type not in disallow_updates:
                try:
                    ci.update_object(object_type=self.object_type,
                                    partial_url=self.partial_URL,
                                    data=backing_data)
                except HTTPError as e:
                    logger.info("Could not PATCH object: {0}".format(e))

    def patch_backup(self, backing_data):
        # PATCH the fields in back.
        logger.info("Trying to PATCH object...")
        if self.partial_URL:
            if self.object_type not in self.disallow_updates:
                logger.debug("partial_url: {0}".format(self.partial_URL))
                try:
                    ci.update_object(object_type=self.object_type,
                                    partial_url=self.partial_URL,
                                    data=backing_data)
                except HTTPError as e:
                    logger.info("Could not PATCH object: {0}".format(e))
        else:
            # No partial URL, object is to be completely backed up
            self.create_backup(backing_data)

    def process_on_save_signal(self, sender, **kwargs):
        """
        After saving the object locally, we sync the
        changes to the remotely backed layer as well.
        """
        logger.info("Inside AbstractRemotelyBackedObject!")

        backing_data = self.prepare_backing_data()
        # handle object get/create
        try:
            if kwargs.get('created'):
                self.create_backup(backing_data)
            else:
                self.patch_backup(backing_data)
            super(AbstractRemotelyBackedObject, self).process_on_save_signal(sender, **kwargs)
        except MailmanConnectionError as e:
            logger.info("Could not back up properly: {0}".format(e))


class AbstractRemotelyBackedDefault(AbstractRemotelyBackedObject):
    class Meta:
        abstract = True

    def process_on_save_signal(self, sender, **kwargs):
        backing_data = self.prepare_backing_data()
        try:
            if kwargs.get('created'):
                # Don't back up anything, we already have defaults.
                pass
            else:
                self.patch_backup(backing_data)
            super(AbstractRemotelyBackedDefault, self).process_on_save_signal(sender, **kwargs)
        except MailmanConnectionError as e:
            logger.info("Could not back up properly: {0}".format(e))

