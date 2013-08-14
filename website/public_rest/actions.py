#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db.models.signals import post_save
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

@receiver(post_save, sender=User)
def on_User_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)

@receiver(post_save, sender=Domain)
def on_Domain_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)

@receiver(post_save, sender=Email)
def on_Email_save(sender, **kwargs):
    kwargs['instance'].process_on_save_signal(sender, **kwargs)
