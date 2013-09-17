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
from rest_framework.test import APILiveServerTestCase, APIClient

from public_rest.models import *

from django.conf import settings
from public_rest.api import CoreInterface

from urlparse import urlsplit
import requests
import json
import os
import time

setup_test_environment()

import logging
logging.disable(logging.INFO)   # logging.DEBUG


class ModelTest(TestCase):

    '''
    @classmethod
    def setUpClass(cls):
        """Setup a fresh copy of the Mailman core database."""
        # If -core is running, stop it
        try:
            stop_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','stop_mailman'))
            os.system(stop_command)
        except:
            pass
        # Start a new copy of -core
        start_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','start_mailman'))
        os.system(start_command)
        time.sleep(2)
        # Give it some time to start
        core = Connection()
        tries = 1
        while tries > 0:
            try:
                core.call('system')
                print ('tries = {0}'.format(tries))
                tries = -1
            except MailmanConnectionError:
                tries = tries +1
                time.sleep(1)
                if tries > 15:
                    raise Exception('Mailman-core failed to start')

    @classmethod
    def tearDownClass(cls):
        """Remove the Mailman core database after tests are complete."""
        # Stop -core
        stop_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','stop_mailman'))
        os.system(stop_command)
    '''

    def setUp(self):
        """
        For *every* test, we need at least a User object.
        """
        # Create a user
        u = get_user_model().objects.create(display_name='Test Admin',
                                            email='admin@test.com',
                                            password='password')
        # Create a domain
        d = Domain.objects.create(base_url='example.com',
                                  mail_host='mail.example.com',
                                  description='An example domain',
                                  contact_address='admin@example.com')
        super(ModelTest, self).setUp()

    def tearDown(self):
        admin_user = User.objects.get(display_name='Test Admin')
        admin_user.delete()
        for l in MailingList.objects.all(): l.delete()
        d = Domain.objects.get(mail_host='mail.example.com')
        d.delete()
        super(ModelTest, self).tearDown()

    def setup_list(self):
        """
        Create a mock domain, list and a user.
        """
        domain = Domain.objects.get(mail_host='mail.example.com')
        mlist = domain.create_list('test')
        return domain, mlist

    def create_subscription(self, user, mlist, role='member'):
        """
        Associate the user and list with a subscription.
        """
        email = user.preferred_email
        sub = Membership.objects.create(user=user, mlist=mlist, address=email, role=role)
        return sub


    def test_user_password(self):
        u = User.objects.get(display_name='Test Admin')
        self.assertTrue(u.check_password('password'))

    def test_user_preferences(self):
        """A User should have preferences"""
        user = User.objects.get(display_name='Test Admin')
        prefs = user.preferences
        self.assertIsNotNone(prefs)
        self.assertIsInstance(prefs, UserPrefs)

    def test_user_email_preferences(self):
        """Test the email preferences related to the User"""
        user = User.objects.get(display_name='Test Admin')
        prefs = user.preferred_email.preferences
        self.assertIsNotNone(prefs)
        self.assertIsInstance(prefs, EmailPrefs)

    def test_email_preferences(self):
        """Test email preferences solo"""
        email = Email.objects.create(address='eidolon@triumvirate.com')
        prefs = email.preferences
        self.assertIsNotNone(prefs)
        self.assertIsInstance(prefs, EmailPrefs)

    def test_preferred_email(self):
        u = User.objects.create(display_name='naeblis',
                                email='pref@example.com',
                                password='12345')
        self.assertEqual(u.preferred_email.address, 'pref@example.com')
        u.create_preferred_email(address='foo@bar.com')
        self.assertEqual(u.preferred_email.address, 'foo@bar.com')

    def test_domain(self):
        d = Domain.objects.get(mail_host='mail.example.com')
        self.assertEqual(d.base_url, 'example.com')
        self.assertEqual(d.mail_host, 'mail.example.com')
        self.assertEqual(d.description, 'An example domain')
        self.assertEqual(d.contact_address, 'admin@example.com')

    def test_empty_domain(self):
        d = Domain.objects.create()
        self.assertEqual(d.base_url, 'http://')
        self.assertEqual(d.mail_host, '')
        self.assertEqual(d.description, '')
        self.assertEqual(d.contact_address, '')

    def test_list(self):
        d = Domain.objects.get(mail_host='mail.example.com')
        mlist = d.create_list('test')
        self.assertEqual(d.description, 'An example domain')
        self.assertEqual(mlist.list_name, 'test')
        self.assertEqual(mlist.mail_host, 'mail.example.com')
        self.assertEqual(mlist.fqdn_listname, 'test@mail.example.com')
        self.assertEqual(mlist.domain, d)
        self.assertEqual(mlist.owners.count(), 0)
        #### TODO: The User for the next address has not been created yet
        mlist.subscribe('a@example.com')
        self.assertTrue('a@example.com' in [email.address.address for email in mlist.members])
        mlist.add_owner('batman@gotham.com')
        self.assertTrue('batman@gotham.com' in [email.address.address for email in mlist.owners])
        mlist.add_moderator('superman@metropolis.com')
        self.assertTrue('superman@metropolis.com' in [email.address.address for email in mlist.moderators])
        # also present in all_subscribers
        self.assertTrue('a@example.com' in [email.address.address for email in mlist.all_subscribers])
        self.assertTrue('batman@gotham.com' in [email.address.address for email in mlist.all_subscribers])
        self.assertTrue('superman@metropolis.com' in [email.address.address for email in mlist.all_subscribers])

    def test_user(self):
        u = get_user_model().objects.create(display_name='testuser',
                                            email='test@user.com',
                                            password='hellogoodbye')
        self.assertEqual(u.emails.count(), 1)
        u_mail = u.add_email('hello@goodbye.com')
        self.assertEqual(u.emails.count(), 2)
        with self.assertRaises(ValueError):
            self.assertIsNone(u.add_email('hello@goodbye.com'))   # Can't add the same address twice.
            self.assertEqual(u.emails.count(), 2)                 # so no new email
        self.assertEqual(u.get_email('hello@goodbye.com'), u_mail)
        u.set_password('foobar')
        self.assertTrue(u.check_password('foobar'))

    def test_subscriber_creation(self):
        domain, mlist = self.setup_list()
        user = User.objects.get(display_name='Test Admin')
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
        domain, mlist = self.setup_list()
        sub = mlist.add_member('test@mail.example.com')
        prefs = sub.preferences

        self.assertIsInstance(sub, Membership)
        self.assertIsNotNone(prefs)
        self.assertIsInstance(prefs, MembershipPrefs)
        self.assertIsInstance(prefs, MembershipPrefs)
        self.assertIsNone(prefs['receive_list_copy'])
        self.assertIsNone(prefs['acknowledge_posts'])
        self.assertIsNone(prefs['receive_list_copy'])
        self.assertIsNone(prefs['receive_own_postings'])
        self.assertIsNone(prefs['hide_address'])
        self.assertEqual(prefs['delivery_mode'], '')
        self.assertEqual(prefs['delivery_status'], '')
        self.assertEqual(prefs['preferred_language'], '')

    def test_subscriber_preferences_persistence(self):
        """Test that membership preferences are actually linked to the object itself."""
        domain, mlist = self.setup_list()
        self.assertEqual(MembershipPrefs.objects.count(), 0)

        sub = mlist.add_member('test2@mail.example.com')
        prefs = sub.preferences

        self.assertEqual(MembershipPrefs.objects.count(), 1)
        self.assertIsInstance(sub, Membership)
        self.assertIsNotNone(prefs)
        self.assertIsInstance(prefs, MembershipPrefs)

        sub = Membership.objects.get(address__address='test2@mail.example.com',
                                            mlist=mlist,
                                            role='member')
        self.assertIsNotNone(sub.preferences)
        self.assertIsInstance(sub.preferences, MembershipPrefs)


    def test_list_settings(self):
        domain, mlist = self.setup_list()
        user = User.objects.get(display_name='Test Admin')
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


class DRFTestCase(APILiveServerTestCase):

    def setUp(self):
        u = get_user_model().objects.create_superuser(display_name='Test Admin',
                                                      email='admin@test.com',
                                                      password='password')

        d = Domain.objects.create(base_url='http://example.com',
                                  mail_host='mail.example.com',
                                  description='An example domain',
                                  contact_address='admin@example.com')

        self.client = APIClient()
        self.client.login(username='Test Admin', password='password')

        mlist = d.create_list(list_name='test_list')
        mlist.add_owner(u.preferred_email)

    def tearDown(self):
        self.client.logout()


    def test_get_HTTP_response(self):
        """Test that the REST API is operative"""
        # Get something
        res = self.client.get('/api/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)


    def test_get_domain_collection(self):
        res = self.client.get('/api/domains/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['count'], 1)
        domain = res_json['results'][0]
        self.assertEqual(domain['mail_host'], 'mail.example.com')
        self.assertEqual(domain['base_url'], 'http://example.com')


    def test_get_individual_domain(self):
        res = self.client.get('/api/domains/1/')
        self.assertEqual(res.status_code, 200)
        domain = json.loads(res.content)
        self.assertEqual(domain['mail_host'], 'mail.example.com')
        self.assertEqual(domain['base_url'], 'http://example.com')
        self.assertEqual(domain['description'], 'An example domain')
        self.assertEqual(domain['contact_address'], 'admin@example.com')


    def test_create_new_domain(self):
        res = self.client.post('/api/domains/', data={'mail_host': 'mail.foobar.com'})
        self.assertEqual(res.status_code, 201)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['mail_host'], 'mail.foobar.com')
        self.assertEqual(res_json['base_url'], 'http://mail.foobar.com')


    def test_delete_domain(self):
        res = self.client.get('/api/domains/1/')
        self.assertEqual(res.status_code, 200)
        res = self.client.delete('/api/domains/1/')
        self.assertEqual(res.status_code, 204)
        res = self.client.get('/api/domains/1/')
        self.assertEqual(res.status_code, 404)


    def test_get_list_collection(self):
        res = self.client.get('/api/lists/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['count'], 1)
        mlist = res_json['results'][0]
        self.assertEqual(mlist['fqdn_listname'], 'test_list@mail.example.com')
        self.assertEqual(mlist['list_name'], 'test_list')


    def test_get_individual_list(self):
        res = self.client.get('/api/lists/1/')
        self.assertEqual(res.status_code, 200)
        mlist = json.loads(res.content)
        self.assertEqual(mlist['fqdn_listname'], 'test_list@mail.example.com')
        self.assertEqual(mlist['list_name'], 'test_list')
        self.assertIsInstance(mlist['members'], list)
        self.assertIsInstance(mlist['owners'], list)
        self.assertIsInstance(mlist['moderators'], list)


    def test_create_new_list(self):
        res = self.client.post('/api/lists/', data={'list_name': 'new_list',
            'mail_host': 'mail.example.com'})
        self.assertEqual(res.status_code, 201)
        mlist = json.loads(res.content)
        self.assertEqual(mlist['fqdn_listname'], 'new_list@mail.example.com')
        self.assertEqual(mlist['list_name'], 'new_list')


    def test_delete_list(self):
        res = self.client.get('/api/lists/1/')
        self.assertEqual(res.status_code, 200)
        res = self.client.delete('/api/lists/1/')
        self.assertEqual(res.status_code, 204)
        res = self.client.get('/api/lists/1/')
        self.assertEqual(res.status_code, 404)


    def test_get_list_settings(self):
        #from django.core.management import call_command
        #call_command('dumpdata', 'public_rest.listsettings')
        res = self.client.get('/api/lists/1/')
        res_json = json.loads(res.content)
        url = urlsplit(res_json['settings']).path
        res = self.client.get(url)
        res_json = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res_json['admin_immed_notify'])


    def test_modify_list_settings(self):
        res = self.client.get('/api/lists/1/settings/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['admin_immed_notify'], True)
        self.assertEqual(res_json['autoresponse_owner_text'], '')

        res = self.client.patch('/api/lists/1/settings/',
                                data={'admin_immed_notify': 'false',
                                'autoresponse_owner_text': 'THIS IS SPARTA!'})

        self.assertEqual(res.status_code, 204)

        res = self.client.get('/api/lists/1/settings/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['admin_immed_notify'], False)
        self.assertEqual(res_json['autoresponse_owner_text'], 'THIS IS SPARTA!')


    def test_pagination_on_custom_endpoint(self):
        """All secondary/tertiary... endpoints should have paginated responses"""
        # no members initially
        res = self.client.get('/api/lists/1/members/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertTrue(res_json.has_key('results'))
        self.assertEqual(len(res_json['results']), 0)

        # add a member
        res = self.client.post('/api/lists/1/members/', data={'address': 'newmember@foobar.com'})
        self.assertEqual(res.status_code, 201)
        res = self.client.get('/api/lists/1/members/')
        res_json = json.loads(res.content)
        self.assertIsInstance(res_json, dict)
        self.assertTrue(res_json.has_key('count'))
        self.assertTrue(res_json.has_key('prev'))
        self.assertTrue(res_json.has_key('next'))
        self.assertTrue(res_json.has_key('results'))


    def test_make_list_subscription(self):
        """
        Subscribe a new membership to an existing list.
        This ofcourse assumes valid permissions.
        """
        # new member
        res = self.client.post('/api/lists/1/members/', data={'address':'newmember@foobar.com'})
        self.assertEqual(res.status_code, 201)

        # new moderator
        res = self.client.post('/api/lists/1/moderators/', data={'address':'newmoderator@foobar.com'})
        self.assertEqual(res.status_code, 201)

        # new owner
        res = self.client.post('/api/lists/1/owners/', data={'address':'newowner@foobar.com'})
        self.assertEqual(res.status_code, 201)


    def test_make_list_subscription_permissions(self):
        """
        Not everyone is allowed to just create any kind of memberships!
        """
        # Create a non-staff user and login
        u = User.objects.create(display_name='RandomUser', email='random@user.com',
                password='password')
        u.add_email('rand1@email.com')
        u.add_email('rand2@email.com')
        u.add_email('rand3@email.com')

        self.client.logout()
        self.client.login(username='RandomUser', password='password')

        res = self.client.post('/api/lists/1/members/')
        self.assertEqual(res.status_code, 201)

        res = self.client.post('/api/lists/1/members/', data={'address':'rand1@email.com'})
        self.assertEqual(res.status_code, 201)

        res = self.client.post('/api/lists/1/members/', data={'address':'rand2@email.com',
                                                              'user': 'RandomUser'})
        self.assertEqual(res.status_code, 201)

        # Invalid data
        res = self.client.post('/api/lists/1/members/', data={'address':'not_my_email@gmail.com'})
        self.assertEqual(res.status_code, 403)

        res = self.client.post('/api/lists/1/members/', data={'user':'IDoNotExist'})
        self.assertEqual(res.status_code, 404)

        res = self.client.post('/api/lists/1/members/', data={'user':'IDoNotExist',
                                                              'address': 'not_my_email@gmail.com'})

        res = self.client.post('/api/lists/1/members/', data={'user': 'RandomUser',
                                                              'address':'admin@test.com'})
        self.assertEqual(res.status_code, 400)

        # valid data (but no permissions)
        res = self.client.post('/api/lists/1/members/', data={'user':'Test Admin',
                                                              'address': 'admin@test.com'})
        self.assertEqual(res.status_code, 403)

        res = self.client.post('/api/lists/1/members/', data={'user':'Test Admin'})
        self.assertEqual(res.status_code, 403)

        res = self.client.post('/api/lists/1/members/', data={'address':'admin@test.com'})
        self.assertEqual(res.status_code, 403)

        res = self.client.post('/api/lists/1/owners/', data={'address':'rand1@email.com'})
        self.assertEqual(res.status_code, 403)

        res = self.client.post('/api/lists/1/moderators/', data={'address':'rand1@email.com'})
        self.assertEqual(res.status_code, 403)


        self.client.logout()


    def test_get_individual_subscription(self):
        res = self.client.post('/api/lists/1/members/', data={'address':'newmember@foobar.com'})
        self.assertEqual(res.status_code, 201)

        # get the subscription at its own url
        res = self.client.get('/api/lists/1/members/newmember@foobar.com/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['role'], 'member')
        self.assertIsInstance(res_json['mlist'], dict)
        mlist_path = urlsplit(res_json['mlist']['url']).path
        self.assertEqual(mlist_path, '/api/lists/1/')
        user_path = urlsplit(res_json['user']).path
        self.assertEqual(user_path, '/api/users/2/')


    def test_subscription_preferences(self):
        res = self.client.post('/api/lists/1/members/', data={'address':'newmember@foobar.com'})
        self.assertEqual(res.status_code, 201)

        res = self.client.get('/api/lists/1/members/newmember@foobar.com/preferences/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)

        d = {"acknowledge_posts": None,
            "delivery_status": "",
            "delivery_mode": "",
            "hide_address": None,
            "preferred_language": "",
            "receive_list_copy": None,
            "receive_own_postings": None
        }
        for k, v in d.items():
            self.assertEqual(res_json[k], v)

        # Should have its own URL.
        self.assertIsNotNone(res_json['url'])


    def test_update_subscription_preferences(self):
        """Update all or some of the preferences"""
        res = self.client.post('/api/lists/1/members/', data={'address':'newmember@foobar.com'})
        self.assertEqual(res.status_code, 201)

        res = self.client.get('/api/lists/1/members/newmember@foobar.com/preferences/')
        self.assertEqual(res.status_code, 200)

        data={'preferred_language': 'Mandarin',
              'acknowledge_posts': True,
              'delivery_mode': 'plaintext_digests',
              'delivery_status': 'by_user',
              'hide_address': False,
              'preferred_language': 'ja',
              'receive_list_copy': True,
              'receive_own_postings': False
             }

        res = self.client.put('/api/lists/1/members/newmember@foobar.com/preferences/',
                data=data)
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/api/lists/1/members/newmember@foobar.com/preferences/')
        res_json = json.loads(res.content)

        for k, v in data.items():
            self.assertEqual(res_json[k], v)

        # partial update via PATCH
        res = self.client.patch('/api/lists/1/members/newmember@foobar.com/preferences/',
                data={'acknowledge_posts': False})
        self.assertEqual(res.status_code, 204)

        res = self.client.get('/api/lists/1/members/newmember@foobar.com/preferences/')
        res_json = json.loads(res.content)
        self.assertEqual(res_json['acknowledge_posts'], False)


    def test_list_unsubscription(self):
        """Unsubscription from a mailing list"""
        res = self.client.post('/api/lists/1/members/', data={'address':'newmember@foobar.com'})
        self.assertEqual(res.status_code, 201)

        # Can GET
        res = self.client.get('/api/lists/1/members/newmember@foobar.com/')
        self.assertEqual(res.status_code, 200)

        # now unsubscribe
        res = self.client.delete('/api/lists/1/members/newmember@foobar.com/')
        self.assertEqual(res.status_code, 204)

        # further GETs will return 404
        res = self.client.get('/api/lists/1/members/1/')
        self.assertEqual(res.status_code, 404)


    def test_get_user_collection(self):
        res = self.client.get('/api/users/')
        res_json = json.loads(res.content)

        self.assertIsInstance(res_json, dict)
        self.assertEqual(res_json['count'], 1)
        self.assertEqual(res_json['next'], None)
        self.assertEqual(res_json['previous'], None)
        self.assertIsInstance(res_json['results'], list)
        self.assertEqual(len(res_json['results']), 1)

        user = res_json['results'][0]

        self.assertEqual(user['display_name'], 'Test Admin')
        self.assertEqual(user['is_superuser'], True)
        self.assertEqual(urlsplit(user['preferred_email']).path, '/api/emails/1/')
        self.assertEqual(urlsplit(user['url']).path, '/api/users/1/')


    def test_get_individual_user(self):
        res = self.client.get('/api/users/1/')
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['display_name'], 'Test Admin')
        self.assertEqual(res_json['is_superuser'], True)
        self.assertEqual(urlsplit(res_json['preferred_email']).path, '/api/emails/1/')
        self.assertEqual(urlsplit(res_json['url']).path, '/api/users/1/')
        self.assertIsInstance(res_json['emails'], list)
        self.assertEqual(res_json['emails'][0], 'admin@test.com')


    def test_create_new_user(self):
        res = self.client.post('/api/users/', data={'display_name':'Thor',
                                                    'email':'son_of_odin@asgard.com',
                                                    'password':'Mjöllnir'})
        self.assertEqual(res.status_code, 201)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['display_name'], 'Thor')
        self.assertEqual(res_json['is_superuser'], False)


    def test_get_user_subscriptions(self):
        """Get all the subscriptions related to a user"""

        # Create a user
        res = self.client.post('/api/users/', data={'display_name':'Odin',
                                                    'email': 'boss@asgard.com',
                                                    'password': 'Wednesday'})
        self.assertEqual(res.status_code, 201)
        user_path = urlsplit(json.loads(res.content)['url']).path

        # Create a new subscription related to this user
        res = self.client.post('/api/lists/1/members/', data={'user':'Odin'})  # will use the preferred_email
        self.assertEqual(res.status_code, 201)

        # now test
        res = self.client.get('{0}subscriptions/'.format(user_path))
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        #logger.error("\nUser Subscriptions:{0}".format(res_json))
        #XXX: Ideally, this result should be paginated, but we're
        # skipping that for the real testing now.
        self.assertIsInstance(res_json, list)
        sub1 = res_json[0]
        self.assertEqual(sub1['address'], 'boss@asgard.com')
        self.assertEqual(sub1['role'], 'member')
        self.assertEqual(sub1['user'], 'Odin')
        self.assertEqual(sub1['mlist'], 'test_list')


    def test_user_subscriptions_permissions(self):
        """
        Admin can view all of them, but list owners/moderators
        can only view subscriptions related to their own lists for a user.
        """
        # Create a new list, with a new owner etc.
        res = self.client.post('/api/lists/', data={'list_name':'newlist',
            'mail_host': 'mail.example.com'})
        self.assertEqual(res.status_code, 201)
        res_json = json.loads(res.content)
        list_path = urlsplit(res_json['url']).path

        # Setup a few users to test things later.
        u = self.client.post('/api/users/', data=dict(display_name='newuser',
                                                       password='password',
                                                       email='newuser@foo.com'))
        self.assertEqual(u.status_code, 201)
        res_json = json.loads(u.content)
        user_path = urlsplit(res_json['url']).path

        # Add the user as an owner and a subscriber
        res = self.client.post('{0}owners/'.format(list_path), data={'address': 'newuser@foo.com'})
        res = self.client.post('{0}members/'.format(list_path), data={'address': 'newuser@foo.com'})
        self.assertEqual(res.status_code,201)

        # If we have an owner/mod for a separate list, she can not
        # view this user's subscription for newlist.
        u2 = self.client.post('/api/users/', data=dict(display_name='separate_user',
                                                        password='password',
                                                        email='separate@user.com'))
        self.assertEqual(u2.status_code, 201)

        # Regular user who is not a subscriber to any list at all.
        u3 = self.client.post('/api/users/', data=dict(display_name='RegularJoe',
                                                       password='password',
                                                       email='regular@user.com'))
        self.assertEqual(u3.status_code, 201)


        newlist = self.client.post('/api/lists/', data={'mail_host': 'mail.example.com',
            'list_name': 'newlist2'})
        self.assertEqual(newlist.status_code, 201)
        res_json = json.loads(newlist.content)
        newlist_path = urlsplit(res_json['url']).path

        # add as owner
        res = self.client.post('{0}owners/'.format(newlist_path), data={'address': 'separate@user.com'})
        self.assertEqual(res.status_code, 201)

        # newuser can only view subscriptions for users on newlist.
        self.client.logout()
        self.client.login(username='newuser', password='password')

        res = self.client.get('{0}subscriptions/'.format(user_path))
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(len(res_json), 1)
        self.assertEqual(res_json[0]['address'], 'newuser@foo.com')

        self.client.logout()
        self.client.login(username='separate_user', password='password')
        res = self.client.get('{0}subscriptions/'.format(user_path))
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(len(res_json), 0)

        # Regular members just get 403
        self.client.logout()
        self.client.login(username='RegularJoe', password='password')

        res = self.client.get('{0}subscriptions/'.format(user_path))
        self.assertEqual(res.status_code, 403)

        self.client.logout()


    def test_delete_user(self):
        # Create a user
        res = self.client.post('/api/users/', data={'display_name': 'Zeus',
                                                    'email': 'ladies_love@olympus.com',
                                                    'password':'Titans_Suck!'})
        self.assertEqual(res.status_code, 201)
        user_path = urlsplit(json.loads(res.content)['url']).path

        res = self.client.get(user_path)
        self.assertEqual(res.status_code, 200)
        res = self.client.delete(user_path)
        self.assertEqual(res.status_code, 204)
        res = self.client.get(user_path)
        self.assertEqual(res.status_code, 404)


    def test_get_user_emails(self):
        """Access all the emails associated with the user"""
        res = self.client.post('/api/users/', data={'display_name': 'Zeus',
                                                    'email': 'god@olympus.com',
                                                    'password':'Titans_Suck!'})
        self.assertEqual(res.status_code, 201)
        user_path = urlsplit(json.loads(res.content)['url']).path

        res = self.client.get('{0}emails/'.format(user_path))
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        #XXX
        self.assertIsInstance(res_json, list)
        self.assertEqual(res_json[0]['address'], 'god@olympus.com')
        self.assertEqual(res_json[0]['verified'], False)
        self.assertEqual(res_json[0]['user'], 'Zeus')


    def test_add_user_email(self):
        """Add new emails for a user"""
        res = self.client.post('/api/users/', data={'display_name': 'Julius',
                                                    'email': 'general@rome.com',
                                                    'password':'EtTuBrute? :('})
        self.assertEqual(res.status_code, 201)
        user_path = urlsplit(json.loads(res.content)['url']).path

        res = self.client.post('{0}emails/'.format(user_path),
                data={'address': 'gaius@caeser.com'})
        self.assertEqual(res.status_code, 201)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['address'], 'gaius@caeser.com')
        self.assertEqual(res_json['user'], 'Julius')
        self.assertEqual(res_json['verified'], False)


    def test_remove_user_email(self):
        """Email deletion"""
        # Creation
        res = self.client.post('/api/users/', data={'display_name': 'Robert',
                                                    'email': 'director@manhattan.com',
                                                    'password':'IAmBecomeDeath'})
        self.assertEqual(res.status_code, 201)
        user_path = urlsplit(json.loads(res.content)['url']).path

        res = self.client.post('{0}emails/'.format(user_path),
                data={'address': 'oshi@itexplodes.com'})
        self.assertEqual(res.status_code, 201)
        res_json = json.loads(res.content)
        email_path = urlsplit(res_json['url']).path
        # Deletion
        res = self.client.delete(email_path)
        self.assertEqual(res.status_code, 204)
        res = self.client.get(email_path)
        self.assertEqual(res.status_code, 404)


    def test_verify_email(self):
        res = self.client.post('/api/users/', data={'display_name': 'Arjun',
                                                    'email': 'sharpshooter@pandavas.com',
                                                    'password':'ComeAtMeBro!'})
        self.assertEqual(res.status_code, 201)
        email_path = urlsplit(json.loads(res.content)['preferred_email']).path
        # unverified
        res = self.client.get(email_path)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content)['verified'], False)

        # Lets verify it
        res = self.client.post('{0}verify/'.format(email_path), data={})
        self.assertEqual(res.status_code, 204)

        # check
        res = self.client.get(email_path)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content)['verified'], True)


    def test_unverify_email(self):
        res = self.client.post('/api/users/', data={'display_name': 'Harry Dresden',
                                                    'email': 'warden@chicago.com',
                                                    'password':'HellsBells!'})
        self.assertEqual(res.status_code, 201)
        email_path = urlsplit(json.loads(res.content)['preferred_email']).path
        # unverified
        res = self.client.get(email_path)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content)['verified'], False)

        # Lets verify it
        res = self.client.post('{0}verify/'.format(email_path), data={})
        self.assertEqual(res.status_code, 204)

        # check
        res = self.client.get(email_path)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content)['verified'], True)

        # now unverify it.
        res = self.client.post('{0}unverify/'.format(email_path), data={})
        self.assertEqual(res.status_code, 204)

        # check
        res = self.client.get(email_path)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content)['verified'], False)


    def test_get_user_preferences(self):
        pass

    def test_modify_user_preferences(self):
        pass

    def test_login(self):
        pass

    def test_logout(self):
        pass

    def test_permissions(self):
        pass


'''
class CoreTest(TestCase):
    base_url = 'http://localhost:8001/3.0'
    rest_auth = ('restadmin', 'restpass')

    @classmethod
    def setUpClass(cls):
        """Setup a fresh copy of the Mailman core database."""
        # If -core is running, stop it
        try:
            stop_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','stop_mailman'))
            os.system(stop_command)
        except:
            pass
        # Start a new copy of -core
        start_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','start_mailman'))
        os.system(start_command)
        time.sleep(2)
        # Give it some time to start
        core = Connection()
        tries = 1
        while tries > 0:
            try:
                core.call('system')
                print ('tries = {0}'.format(tries))
                tries = -1
            except MailmanConnectionError:
                tries = tries +1
                time.sleep(1)
                if tries > 15:
                    raise Exception('Mailman-core failed to start')

    @classmethod
    def tearDownClass(cls):
        """Remove the Mailman core database after tests are complete."""
        # Stop -core
        stop_command = os.path.abspath(os.path.join(settings.PROJECT_PATH, '..','stop_mailman'))
        os.system(stop_command)

    def create_domain(self):
        url = '{0}/domains'.format(self.base_url)
        res = requests.post(url, data={'mail_host': 'mail.testhost.com'}, auth=self.rest_auth)
        return res

    def create_list(self):
        url = '{0}/lists'.format(self.base_url)
        res = requests.post(url, data={'fqdn_listname': 'newtestlist@mail.testhost.com'}, auth=self.rest_auth)
        return res

    def test_domain_creation(self):
        res = self.create_domain()
        self.assertEqual(res.status_code, 201)

    def test_list_creation(self):
        res = self.create_list()
        self.assertEqual(res.status_code, 201)

'''
