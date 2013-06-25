#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.utils import setup_test_environment
from django.test.client import Client

from public_rest.models import *

setup_test_environment()

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class ModelTest(TestCase):

    def test_domain(self):
        d = Domain.objects.create(base_url='example.com', mail_host='mail.example.com',
                description='An example domain', contact_address='admin@example.com')
        self.assertEqual(d.base_url, 'example.com')
        self.assertEqual(d.mail_host, 'mail.example.com')
        self.assertEqual(d.description, 'An example domain')
        self.assertEqual(d.contact_address, 'admin@example.com')

    def test_empty_domain(self):
        d = Domain.objects.create()
        self.assertEqual(d.base_url, '')
        self.assertEqual(d.mail_host, '')
        self.assertEqual(d.description, '')
        self.assertEqual(d.contact_address, '')

    def test_list(self):
        Domain.objects.create(base_url='example.com', mail_host='mail.example.com',
                description='An example domain', contact_address='admin@example.com')
        d = Domain.objects.get(mail_host='mail.example.com')
        mlist = d.create_list('test')
        self.assertEqual(d.description, 'An example domain')
        self.assertEqual(mlist.fqdn_listname, 'test@mail.example.com')
        self.assertEqual(mlist.domain, d)
        self.assertEqual(mlist.owners.count(), 0)
        mlist.subscribe('a@example.com')
        self.assertTrue('a@example.com' in [email.address for email in mlist.members])
        mlist.add_owner('batman@gotham.com')
        self.assertTrue('batman@gotham.com' in [email.address for email in mlist.owners])
        mlist.add_moderator('superman@metropolis.com')
        self.assertTrue('superman@metropolis.com' in [email.address for email in mlist.moderators])
        # also present in all_subscribers
        self.assertTrue('a@example.com' in [email.address for email in mlist.all_subscribers])
        self.assertTrue('batman@gotham.com' in [email.address for email in mlist.all_subscribers])
        self.assertTrue('superman@metropolis.com' in [email.address for email in mlist.all_subscribers])

    def test_user(self):
        u = User.objects.create()
        self.assertEqual(u.emails.count(), 0)
        u_mail = u.add_email('hello@goodbye.com')
        self.assertEqual(u.emails.count(), 1)
        self.assertIsNone(u.add_email('hello@goodbye.com'))   # Can't add the same address twice.
        self.assertEqual(u.emails.count(), 1)                 # so no new email
        #self.assertEqual(u.get_email('hello@goodbye.com'), u_mail)
        u.set_password('foobar')
        self.assertTrue(u.check_password('foobar'))

    def test_subscriber_creation(self):
        domain = Domain.objects.create(base_url='example.com', mail_host='mail.example.com')
        mlist = domain.create_list('test')
        user = User.objects.create()
        sub1 = Subscriber.objects.create(user=user, _list=mlist, address='admin@example.com', role='member')
        self.assertTrue(sub1.is_member())
        self.assertFalse(sub1.is_owner())
        self.assertFalse(sub1.is_moderator())
        sub2 = Subscriber.objects.create(user=user, _list=mlist, address='admin@example.com', role='owner')
        self.assertFalse(sub2.is_member())
        self.assertTrue(sub2.is_owner())
        self.assertFalse(sub2.is_moderator())
        sub3 = Subscriber.objects.create(user=user, _list=mlist, address='admin@example.com', role='moderator')
        self.assertFalse(sub3.is_member())
        self.assertFalse(sub3.is_owner())
        self.assertTrue(sub3.is_moderator())


