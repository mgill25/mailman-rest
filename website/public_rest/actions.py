#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from public_rest.signals import sig_email, sig_user
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

def before_Email_delete(sender, instance, **kwargs):
    user = instance.user
    preferred = user.preferred_email
    if kwargs.get('cascade') == False and preferred and instance.address == preferred.address:
        if user.email_set.count() == 1:
            raise ValueError("Only email associated with user")
        email = user.email_set.exclude(address=preferred.address)[0]
        user.preferred_email = email
        user.save()

sig_email.connect(before_Email_delete)


@receiver(pre_delete, sender=User)
def before_User_delete(sender, instance, **kwargs):
    """
    Set preferred_email to None so that
    email deletion is simpler.
    """
    instance.preferred_email = None
    instance.backup = False
    instance.save()

