#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth import get_user_model
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

    def create_sample_user(self):
        u = get_user_model()(display_name='James Bond')
        u.save()
        u.set_password('casino')
        return u

    def setup_list_user(self):
        """
        Create a mock domain, list and a user.
        """
        domain = Domain.objects.create(base_url='example.com', mail_host='mail.example.com')
        mlist = domain.create_list('test')
        user = self.create_sample_user()
        return domain, mlist, user

    def test_user_password(self):
        u = self.create_sample_user()
        self.assertTrue(u.check_password('casino'))

    def create_subscription(self, user, mlist, role='member'):
        """
        Associate the user and list with a subscription.
        """
        sub = Membership.objects.create(user=user, mlist=mlist, address='admin@example.com', role=role)
        return sub

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
        self.assertEqual(mlist.list_name, 'test')
        self.assertEqual(mlist.mail_host, 'mail.example.com')
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
        u = get_user_model().objects.create()
        self.assertEqual(u.emails.count(), 0)
        u_mail = u.add_email('hello@goodbye.com')
        self.assertEqual(u.emails.count(), 1)
        with self.assertRaises(ValueError):
            self.assertIsNone(u.add_email('hello@goodbye.com'))   # Can't add the same address twice.
            self.assertEqual(u.emails.count(), 1)                 # so no new email
        #self.assertEqual(u.get_email('hello@goodbye.com'), u_mail)
        u.set_password('foobar')
        self.assertTrue(u.check_password('foobar'))

    def test_subscriber_creation(self):
        domain, mlist, user = self.setup_list_user()
        sub1 = self.create_subscription(user, mlist, 'member')
        self.assertTrue(sub1.is_member())
        self.assertFalse(sub1.is_owner())
        self.assertFalse(sub1.is_moderator())
        sub2 = self.create_subscription(user, mlist, 'owner')
        self.assertFalse(sub2.is_member())
        self.assertTrue(sub2.is_owner())
        self.assertFalse(sub2.is_moderator())
        sub3 = self.create_subscription(user, mlist, 'moderator')
        self.assertFalse(sub3.is_member())
        self.assertFalse(sub3.is_owner())
        self.assertTrue(sub3.is_moderator())

    def test_subscriber_preferences_empty(self):
        domain, mlist, user = self.setup_list_user()
        sub = self.create_subscription(user, mlist, 'member')
        prefs = sub.preferences
        self.assertIsNone(prefs['receive_list_copy'])
        self.assertIsNone(prefs['acknowledge_posts'])
        self.assertIsNone(prefs['receive_list_copy'])
        self.assertIsNone(prefs['receive_own_postings'])
        self.assertIsNone(prefs['hide_address'])
        self.assertEqual(prefs['delivery_mode'], '')
        self.assertEqual(prefs['delivery_status'], '')
        self.assertEqual(prefs['preferred_language'], '')

    def test_list_settings(self):
        domain, mlist, user = self.setup_list_user()
        mset = mlist.settings
        self.assertTrue(mset.admin_immed_notify)
        self.assertFalse(mset.admin_notify_mchanges)
        self.assertEqual(mset.archive_policy, "public")
        self.assertTrue(mset.administrivia)
        self.assertTrue(mset.advertised)
        self.assertTrue(mset.allow_list_posts)
        self.assertFalse(mset.anonymous_list)
        self.assertEqual(mset.autorespond_owner, "none")
        self.assertEqual(mset.autoresponse_owner_text, "")
        self.assertEqual(mset.autorespond_postings, "none")
        self.assertEqual(mset.autoresponse_postings_text, "")
        self.assertEqual(mset.autorespond_requests, "none")
        self.assertEqual(mset.autoresponse_request_text, "")
        self.assertTrue(mset.collapse_alternatives)
        self.assertFalse(mset.convert_html_to_plaintext)
        self.assertFalse(mset.filter_content)
        self.assertFalse(mset.first_strip_reply_to)
        self.assertTrue(mset.include_rfc2369_headers)
        self.assertEqual(mset.reply_goes_to_list, "no_munging")
        self.assertTrue(mset.send_welcome_message)
        self.assertEqual(mset.display_name, "")
        self.assertEqual(mset.bounces_address, 'test-bounces@mail.example.com')
        self.assertEqual(mset.default_member_action, 'defer')
        self.assertEqual(mset.default_nonmember_action, 'hold')
        self.assertEqual(mset.description, '')
        self.assertEqual(mset.digest_size_threshold, 30.0)
        self.assertEqual(mset.http_etag, '')
        self.assertEqual(mset.join_address, 'test-join@mail.example.com')
        self.assertEqual(mset.leave_address, 'test-leave@mail.example.com')
        self.assertEqual(mset.mail_host, 'mail.example.com')
        self.assertEqual(mset.next_digest_number, 1)
        self.assertEqual(mset.no_reply_address, 'noreply@mail.example.com')
        self.assertEqual(mset.owner_address, 'test-owner@mail.example.com')
        self.assertEqual(mset.post_id, 1)
        self.assertEqual(mset.posting_address, '')
        self.assertEqual(mset.posting_pipeline, 'default-posting-pipeline')
        self.assertEqual(mset.reply_to_address, '')
        self.assertEqual(mset.request_address, 'test-request@mail.example.com')
        self.assertEqual(mset.scheme, '')
        self.assertEqual(mset.volume, 1)
        self.assertEqual(mset.subject_prefix, '')
        self.assertEqual(mset.web_host, '')
        self.assertEqual(mset.welcome_message_uri, 'mailman:///welcome.txt')
