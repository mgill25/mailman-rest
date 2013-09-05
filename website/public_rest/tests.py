#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run these tests with "manage.py test".
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase, LiveServerTestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.test.utils import setup_test_environment

from public_rest.models import *

from django.conf import settings
from public_rest.api import CoreInterface

from urlparse import urlsplit
import json
import os
import time

setup_test_environment()

#class ModelTest(TestCase):
#
#    @classmethod
#    def setUpClass(cls):
#        """Setup a fresh copy of the Mailman core database."""
#        # If -core is running, stop it
#        try:
#            stop_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','stop_mailman'))
#            os.system(stop_command)
#        except:
#            pass
#        # Start a new copy of -core
#        start_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','start_mailman'))
#        os.system(start_command)
#        time.sleep(2)
#        # Give it some time to start
#        core = Connection()
#        tries = 1
#        while tries > 0:
#            try:
#                core.call('system')
#                print ('tries = {0}'.format(tries))
#                tries = -1
#            except MailmanConnectionError:
#                tries = tries +1
#                time.sleep(1)
#                if tries > 15:
#                    raise Exception('Mailman-core failed to start')
#
#    @classmethod
#    def tearDownClass(cls):
#        """Remove the Mailman core database after tests are complete."""
#        # Stop -core
#        stop_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','stop_mailman'))
#        os.system(stop_command)
#
#    def setUp(self):
#        """
#        For *every* test, we need at least a User object.
#        """
#        # Create a user
#        u = get_user_model().objects.create(display_name='Test Admin',
#                                            email='admin@test.com',
#                                            password='password')
#        # Create a domain
#        d = Domain.objects.create(base_url='example.com',
#                                  mail_host='mail.example.com',
#                                  description='An example domain',
#                                  contact_address='admin@example.com')
#        super(ModelTest, self).setUp()
#
#    def tearDown(self):
#        # delete user
#        admin_user = User.objects.get(display_name='Test Admin')
#        admin_user.delete()
#        # delete domain
#        d = Domain.objects.get(mail_host='mail.example.com')
#        d.delete()
#        super(ModelTest, self).tearDown()
#
#    def setup_list(self):
#        """
#        Create a mock domain, list and a user.
#        """
#        domain = Domain.objects.get(mail_host='mail.example.com')
#        mlist = domain.create_list('test')
#        return domain, mlist
#
#    def create_subscription(self, user, mlist, role='member'):
#        """
#        Associate the user and list with a subscription.
#        """
#        email, created = Email.objects.get_or_create(address='admin@example.com')
#        sub = Membership.objects.create(user=user, mlist=mlist, address=email, role=role)
#        return sub
#
#    def test_user_password(self):
#        u = User.objects.get(display_name='Test Admin')
#        self.assertTrue(u.check_password('password'))
#
#    def test_user_preferences(self):
#        """A User should have preferences"""
#        user = User.objects.get(display_name='Test Admin')
#        prefs = user.preferences
#        self.assertIsNotNone(prefs)
#        self.assertIsInstance(prefs, UserPrefs)
#
#    def test_user_email_preferences(self):
#        """Test the email preferences related to the User"""
#        user = User.objects.get(display_name='Test Admin')
#        prefs = user.preferred_email.preferences
#        self.assertIsNotNone(prefs)
#        self.assertIsInstance(prefs, EmailPrefs)
#
#    def test_email_preferences(self):
#        """Test email preferences solo"""
#        email = Email.objects.create(address='eidolon@triumvirate.com')
#        prefs = email.preferences
#        self.assertIsNotNone(prefs)
#        self.assertIsInstance(prefs, EmailPrefs)
#
#    def test_preferred_email(self):
#        u = User.objects.create(display_name='naeblis',
#                                email='pref@example.com',
#                                password='12345')
#        self.assertEqual(u.preferred_email.address, 'pref@example.com')
#        u.create_preferred_email(address='foo@bar.com')
#        self.assertEqual(u.preferred_email.address, 'foo@bar.com')
#
#    def test_domain(self):
#        d = Domain.objects.get(mail_host='mail.example.com')
#        self.assertEqual(d.base_url, 'example.com')
#        self.assertEqual(d.mail_host, 'mail.example.com')
#        self.assertEqual(d.description, 'An example domain')
#        self.assertEqual(d.contact_address, 'admin@example.com')
#
#    def test_empty_domain(self):
#        d = Domain.objects.create()
#        self.assertEqual(d.base_url, '')
#        self.assertEqual(d.mail_host, '')
#        self.assertEqual(d.description, '')
#        self.assertEqual(d.contact_address, '')
#
#    def test_list(self):
#        d = Domain.objects.get(mail_host='mail.example.com')
#        mlist = d.create_list('test')
#        self.assertEqual(d.description, 'An example domain')
#        self.assertEqual(mlist.list_name, 'test')
#        self.assertEqual(mlist.mail_host, 'mail.example.com')
#        self.assertEqual(mlist.fqdn_listname, 'test@mail.example.com')
#        self.assertEqual(mlist.domain, d)
#        self.assertEqual(mlist.owners.count(), 0)
#        #### TODO: The User for the next address has not been created yet
#        mlist.subscribe('a@example.com')
#        self.assertTrue('a@example.com' in [email.address.address for email in mlist.members])
#        mlist.add_owner('batman@gotham.com')
#        self.assertTrue('batman@gotham.com' in [email.address.address for email in mlist.owners])
#        mlist.add_moderator('superman@metropolis.com')
#        self.assertTrue('superman@metropolis.com' in [email.address.address for email in mlist.moderators])
#        # also present in all_subscribers
#        self.assertTrue('a@example.com' in [email.address.address for email in mlist.all_subscribers])
#        self.assertTrue('batman@gotham.com' in [email.address.address for email in mlist.all_subscribers])
#        self.assertTrue('superman@metropolis.com' in [email.address.address for email in mlist.all_subscribers])
#
#    def test_user(self):
#        u = get_user_model().objects.create(display_name='testuser',
#                                            email='test@user.com',
#                                            password='hellogoodbye')
#        self.assertEqual(u.emails.count(), 1)
#        u_mail = u.add_email('hello@goodbye.com')
#        self.assertEqual(u.emails.count(), 2)
#        with self.assertRaises(ValueError):
#            self.assertIsNone(u.add_email('hello@goodbye.com'))   # Can't add the same address twice.
#            self.assertEqual(u.emails.count(), 2)                 # so no new email
#        self.assertEqual(u.get_email('hello@goodbye.com'), u_mail)
#        u.set_password('foobar')
#        self.assertTrue(u.check_password('foobar'))
#
#    def test_subscriber_creation(self):
#        domain, mlist = self.setup_list()
#        user = User.objects.get(display_name='Test Admin')
#        sub1 = self.create_subscription(user, mlist, 'member')
#        self.assertTrue(sub1.is_member())
#        self.assertFalse(sub1.is_owner())
#        self.assertFalse(sub1.is_moderator())
#        sub2 = self.create_subscription(user, mlist, 'owner')
#        self.assertFalse(sub2.is_member())
#        self.assertTrue(sub2.is_owner())
#        self.assertFalse(sub2.is_moderator())
#        sub3 = self.create_subscription(user, mlist, 'moderator')
#        self.assertFalse(sub3.is_member())
#        self.assertFalse(sub3.is_owner())
#        self.assertTrue(sub3.is_moderator())
#
#    def test_subscriber_preferences_empty(self):
#        domain, mlist = self.setup_list()
#        user = User.objects.get(display_name='Test Admin')
#        sub = self.create_subscription(user, mlist, 'member')
#        prefs = sub.preferences
#        self.assertIsNotNone(prefs)
#        self.assertIsInstance(prefs, MembershipPrefs)
#        self.assertIsNone(prefs['receive_list_copy'])
#        self.assertIsNone(prefs['acknowledge_posts'])
#        self.assertIsNone(prefs['receive_list_copy'])
#        self.assertIsNone(prefs['receive_own_postings'])
#        self.assertIsNone(prefs['hide_address'])
#        self.assertEqual(prefs['delivery_mode'], '')
#        self.assertEqual(prefs['delivery_status'], '')
#        self.assertEqual(prefs['preferred_language'], '')
#
#    def test_list_settings(self):
#        domain, mlist = self.setup_list()
#        user = User.objects.get(display_name='Test Admin')
#        mset = mlist.settings
#        self.assertTrue(mset.admin_immed_notify)
#        self.assertFalse(mset.admin_notify_mchanges)
#        self.assertEqual(mset.archive_policy, "public")
#        self.assertTrue(mset.administrivia)
#        self.assertTrue(mset.advertised)
#        self.assertTrue(mset.allow_list_posts)
#        self.assertFalse(mset.anonymous_list)
#        self.assertEqual(mset.autorespond_owner, "none")
#        self.assertEqual(mset.autoresponse_owner_text, "")
#        self.assertEqual(mset.autorespond_postings, "none")
#        self.assertEqual(mset.autoresponse_postings_text, "")
#        self.assertEqual(mset.autorespond_requests, "none")
#        self.assertEqual(mset.autoresponse_request_text, "")
#        self.assertTrue(mset.collapse_alternatives)
#        self.assertFalse(mset.convert_html_to_plaintext)
#        self.assertFalse(mset.filter_content)
#        self.assertFalse(mset.first_strip_reply_to)
#        self.assertTrue(mset.include_rfc2369_headers)
#        self.assertEqual(mset.reply_goes_to_list, "no_munging")
#        self.assertTrue(mset.send_welcome_message)
#        self.assertEqual(mset.display_name, "")
#        self.assertEqual(mset.bounces_address, 'test-bounces@mail.example.com')
#        self.assertEqual(mset.default_member_action, 'defer')
#        self.assertEqual(mset.default_nonmember_action, 'hold')
#        self.assertEqual(mset.description, '')
#        self.assertEqual(mset.digest_size_threshold, 30.0)
#        self.assertEqual(mset.http_etag, '')
#        self.assertEqual(mset.join_address, 'test-join@mail.example.com')
#        self.assertEqual(mset.leave_address, 'test-leave@mail.example.com')
#        self.assertEqual(mset.mail_host, 'mail.example.com')
#        self.assertEqual(mset.next_digest_number, 1)
#        self.assertEqual(mset.no_reply_address, 'noreply@mail.example.com')
#        self.assertEqual(mset.owner_address, 'test-owner@mail.example.com')
#        self.assertEqual(mset.post_id, 1)
#        self.assertEqual(mset.posting_address, '')
#        self.assertEqual(mset.posting_pipeline, 'default-posting-pipeline')
#        self.assertEqual(mset.reply_to_address, '')
#        self.assertEqual(mset.request_address, 'test-request@mail.example.com')
#        self.assertEqual(mset.scheme, '')
#        self.assertEqual(mset.volume, 1)
#        self.assertEqual(mset.subject_prefix, '')
#        self.assertEqual(mset.web_host, '')
#        self.assertEqual(mset.welcome_message_uri, 'mailman:///welcome.txt')
#

class DRFTestCase(LiveServerTestCase):

    def setUp(self):
        u = get_user_model().objects.create_superuser(display_name='Test Admin',
                                                      email='admin@test.com',
                                                      password='password')

        d = Domain.objects.create(base_url='example.com',
                                  mail_host='mail.example.com',
                                  description='An example domain',
                                  contact_address='admin@example.com')

        self.client = Client()
        self.client.login(username='Test Admin', password='password')

    def tearDown(self):
        self.client.logout()

    def test_get_HTTP_response(self):
        """Test that the REST API is operative"""
        # Get something
        res = self.client.get('/api/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)

    def test_list_settings(self):
        """Test List Settings"""
        d = Domain.objects.get(base_url='example.com')
        mlist = d.create_list(list_name='test_list')

        res = self.client.get('/api/lists/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['count'], 1)

        res = self.client.get('/api/lists/1/')
        res_json = json.loads(res.content)
        self.assertEqual(res.status_code, 200)

        logger.debug("*********************************")
        logger.debug(res_json)
        #logger.debug("*********************************")
        from django.core.management import call_command
        call_command('dumpdata', 'public_rest.listsettings')

        url = urlsplit(res_json['settings']).path
        logger.debug("*********************************")
        logger.debug('\nSettings URL: {0}\n'.format(url))
        res = self.client.get(url)
        logger.debug(res.content)
        logger.debug("*********************************")
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        # Test a random setting
        self.assertTrue(res_json['admin_immed_notify'])
