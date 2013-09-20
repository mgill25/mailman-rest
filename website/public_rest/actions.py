#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver

from public_rest.interface import *
from public_rest.models import *
from public_rest.adaptors import *

#   ####################
#     The save actions
#   ####################

@receiver(post_save, sender=MailingList)
def on_MailingList_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)

@receiver(post_save, sender=ListSettings)
def on_ListSettings_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)

@receiver(post_save, sender=User)
def on_User_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)

@receiver(post_save, sender=Domain)
def on_Domain_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)

@receiver(post_save, sender=Membership)
def on_Membership_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)

@receiver(post_save, sender=MembershipPrefs)
def on_MembershipPrefs_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)


#   ######################
#     The delete actions
#   ######################

@receiver(pre_delete, sender=Email)
def before_Email_delete(sender, instance, **kwargs):
    user = instance.user
    if user.email_set.count() == 1:
        raise ValueError("Only email associated with user")

@receiver(post_delete, sender=Email)
def after_Email_delete(sender, instance, **kwargs):
    user = instance.user
    try:
        preferred_email = user.preferred_email
    except Email.DoesNotExist:
        user.preferred_email = user.email_set.all()[0]
        user.save()

