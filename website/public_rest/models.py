import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from urllib2 import HTTPError

from public_rest.adaptors import *
from public_rest.interface import *
from public_rest.api import *

from settings import MAILMAN_API_URL, MAILMAN_USER, MAILMAN_PASS


interface = CoreInterface('%s/3.0/' % MAILMAN_API_URL)
conn = Connection('%s/3.0/' % MAILMAN_API_URL)

class BaseModel(models.Model):
    layer = 'rest'

    class Meta:
        abstract = True


class ListManager(models.Manager):

    def create_list(self, list_name, mail_host, fqdn_listname, **extra_fields):
        if not list_name or not fqdn_listname or not mail_host:
            raise ValueError("Invalid or Absent parameter.")
        now = timezone.now()
        lst = self.model(created_at=now, list_name=list_name, mail_host=mail_host,
                fqdn_listname=fqdn_listname, **extra_fields)
        lst.save()
        return lst

    # Methods to conform to the old Postorius models API.
    def get_or_404(self, **kwargs):
        try:
            rv = self.get(**kwargs)
        except self.model.DoesNotExist:
            raise Http404
        return rv

    def all(self, only_public=False):
        objects = super(ListManager, self).all()
        if only_public:
            public = []
            for obj in objects:
                try:
                    if obj.advertised:
                        public.append(obj)
                except AttributeError:
                    pass
            return public
        else:
            return objects


# List Parameters
class BaseListParamSet(BaseModel):
    """Base Parameters for the List"""
    class Meta:
        abstract = True


class ListConfigParamMixin(BaseListParamSet):
    """Values established at the time that the list is created"""
    class Meta:
        abstract = True


class ListPolicyParamMixin(BaseListParamSet):
    """List policies"""
    class Meta:
        abstract = True

    admin_immed_notify = models.BooleanField(default=True)
    admin_notify_mchanges = models.BooleanField(default=False)
    archive_policy = models.CharField(max_length=50, default=u'public')
    administrivia = models.BooleanField(default=True)
    advertised = models.BooleanField(default=True)
    allow_list_posts = models.BooleanField(default=True)
    anonymous_list = models.BooleanField(default=False)
    autorespond_owner = models.CharField(max_length=50, blank=True, default=u'none')
    autoresponse_owner_text = models.TextField(blank=True)
    autorespond_postings = models.CharField(max_length=50, blank=True, default=u'none')
    autoresponse_postings_text = models.TextField(blank=True)
    autorespond_requests = models.CharField(max_length=50, blank=True, default=u'none')
    autoresponse_request_text = models.TextField(blank=True)
    collapse_alternatives = models.BooleanField(default=True)
    convert_html_to_plaintext = models.BooleanField(default=False)
    filter_content = models.BooleanField(default=False)
    first_strip_reply_to = models.BooleanField(default=False)
    include_rfc2369_headers = models.BooleanField(default=True)
    reply_goes_to_list = models.CharField(max_length=50, default=u'no_munging')
    send_welcome_message = models.BooleanField(default=True)
    display_name = models.CharField(max_length=100)


class ListOperationParamMixin(BaseListParamSet):
    """Values controlling the immediate operations of the list"""
    class Meta:
        abstract = True


    autoresponse_grace_period = models.CharField(max_length=10, default=u'90d')
    bounces_address = models.EmailField()
    default_member_action = models.CharField(max_length=50, default=u'defer')
    default_nonmember_action = models.CharField(max_length=50, default=u'hold')
    description = models.CharField(max_length=100, blank=True)
    digest_size_threshold = models.FloatField(default=30.0)
    http_etag = models.CharField(max_length=50)
    join_address = models.EmailField()
    leave_address = models.EmailField()
    mail_host = models.CharField(max_length=100)
    next_digest_number = models.IntegerField(default=1)
    no_reply_address = models.EmailField()
    owner_address = models.EmailField()
    post_id = models.IntegerField(default=1)
    posting_address = models.EmailField()
    posting_pipeline = models.CharField(max_length=50, default=u'default-posting-pipeline')
    reply_to_address = models.EmailField(blank=True)
    request_address = models.EmailField()
    scheme = models.CharField(max_length=50, default=u'')
    volume = models.IntegerField(default=1)
    subject_prefix = models.CharField(max_length=50)
    web_host = models.CharField(max_length=50, default=u'')
    welcome_message_uri = models.CharField(max_length=50, default=u'mailman:///welcome.txt')

class AcceptableAlias(BaseModel):
    used_by = models.ForeignKey('ListSettings')
    refers_to = models.ForeignKey('MailingList')
    address = models.EmailField(blank=True)

    def __unicode__(self):
        return self.address


class ListParametersMixin(ListConfigParamMixin, ListPolicyParamMixin, ListOperationParamMixin):
    fqdn_listname = models.CharField(max_length=100, unique=True)
    last_post_at = models.DateTimeField(null=True, default=None)
    digest_last_sent_at = models.DateTimeField(null=True, default=None)

    class Meta:
        abstract = True


class ListSettings(ListParametersMixin, AbstractRemotelyBackedObject):
    object_type = 'listsettings'
    lookup_field = 'fqdn_listname'
    adaptor = SettingsAdaptor
    fields = [(name, name) for name in ListParametersMixin._meta.get_all_field_names() if name != u'id']

    @property
    def acceptable_aliases(self):
        return [alias.address for alias in self.acceptablealias_set.all()]

    def add_alias(self, address):
        a, created = AcceptableAlias.objects.get_or_create(used_by=self,
                refers_to=self.mailinglist,
                address=address)
        if created:
            a.save()

    def __iter__(self):
        for field in self._meta.fields:
            yield field.name, getattr(self, field.name)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        setattr(self, key, val)
        self.save()

    def __unicode__(self):
        return self.fqdn_listname

# Mailing List
class AbstractBaseList(BaseModel):
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.list_name


class CoreListMixin(models.Model):
    """Fields that are part of the Mailman core."""
    class Meta:
        abstract = True

    list_name = models.CharField(max_length=100)        # TODO: Verify properties like max-length from MM-core
    mail_host = models.CharField(max_length=100,
            help_text=_("Domain Name hosting this mailing list"))
    fqdn_listname = models.CharField(max_length=100,
            help_text=_("Fully qualified name of the list. It is comprised of list_name + '@' + mail_host"),
            unique=True)
    display_name = models.CharField(max_length=100,
            help_text=_("Human readable name for the mailing list"))

    domain = models.ForeignKey('Domain')
    settings = models.OneToOneField(ListSettings, null=True)

    def save(self, *args, **kwargs):
        """Populate these settings for the current MailingList instance."""
        if self.pk is None:
            # Save the list
            super(CoreListMixin, self).save(*args, **kwargs)
            # Make sure settings are present
            if not self.settings:
                self.settings = ListSettings(fqdn_listname=self.fqdn_listname)
                self.settings.save()
            # Populate
            if not self.settings.join_address:
                self.settings.join_address = u'{0}-join@{1}'.format(self.list_name, self.mail_host)
            if not self.settings.bounces_address:
                self.settings.bounces_address = u'{0}-bounces@{1}'.format(self.list_name, self.mail_host)
            if not self.settings.leave_address:
                self.settings.leave_address = u'{0}-leave@{1}'.format(self.list_name, self.mail_host)
            if not self.settings.no_reply_address:
                self.settings.no_reply_address = u'noreply@{0}'.format(self.mail_host)
            if not self.settings.owner_address:
                self.settings.owner_address = u'{0}-owner@{1}'.format(self.list_name, self.mail_host)
            if not self.fqdn_listname:
                self.fqdn_listname = u'{0}@{1}'.format(self.list_name, self.mail_host)
            if not self.settings.request_address:
                self.settings.request_address = u'{0}-request@{1}'.format(self.list_name, self.mail_host)
            # Postorius is inconsistent in using these via settings or directly
            self.settings.fqdn_listname = self.fqdn_listname
            self.settings.mail_host = self.mail_host
            self.settings.display_name = self.display_name
            self.settings.save()
        super(CoreListMixin, self).save(*args, **kwargs)


class LocalListMixin(models.Model):
    """Fields that are added by us, locally."""

    def save(self, *args, **kwargs):
        if self.pk is None:
            # Create a new list at the given mail_host Domain
            domain = interface.get_domain(mail_host=self.mail_host)
            super(LocalListMixin, self).save(*args, **kwargs)
        else:
            super(LocalListMixin, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class AbstractMailingList(AbstractBaseList, CoreListMixin, LocalListMixin):
    objects = ListManager()

    object_type = 'mailinglist'
    adaptor = ListAdaptor
    fields = [('fqdn_listname', 'fqdn_listname'),]
    lookup_field = 'fqdn_listname'

    class Meta:
        abstract = True

    def defer_message(self, request_id):
        pass

    def subscribe(self, address, role='member'):
        # Check if the address belongs to a user
        try:
            u = get_user_model().objects.get(email__address=address)
        except get_user_model().DoesNotExist as e:
            # The user does not exist, create one, using email as the display_name
            u = get_user_model()(display_name=address)
            u.save()
            e = Email(address=address, user=u)
            e.save()
        # Make a subscription relationship
        s = self.membership_set.create(user=u, address=address, role=role)
        return s

    def unsubscribe(self, address):
        s = self.membership_set.get(address=address)
        s.delete()

    def add_owner(self, address):
        self.subscribe(address, role='owner')

    def add_moderator(self, address):
        self.subscribe(address, role='moderator')

    def add_member(self, address):
        self.subscribe(address, role='member')

    @property
    def owners(self):
        return self.membership_set.filter(role='owner')

    @property
    def moderators(self):
        return self.membership_set.filter(role='moderator')

    @property
    def members(self):
        return self.membership_set.filter(role='member')

    @property
    def all_subscribers(self):
        return self.membership_set.all()

    def get_member(self, address):
        return self.membership_set.get(address=address)

class MailingList(AbstractMailingList, AbstractRemotelyBackedObject):
    class Meta:
        swappable = 'MAILINGLIST_MODEL'


# Domain
class DomainManager(models.Manager):
    def get_or_404(self, **kwargs):
        try:
            rv = self.get(**kwargs)
        except self.model.DoesNotExist:
            raise Http404
        return rv


class Domain(BaseModel, AbstractRemotelyBackedObject):
    object_type='domain'
    keyed_on = 'mail_host'
    lookup_field = 'mail_host'
    adaptor = DomainAdaptor

    objects = DomainManager()

    base_url = models.URLField()
    mail_host = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    contact_address = models.EmailField()

    fields = [('base_url', 'base_url'), ('mail_host', 'mail_host'),
            ('description', 'description'), ('contact_address', 'contact_address')]

    @property
    def lists(self):
        return MailingList.objects.filter(domain=self)

    def create_list(self, list_name, **kwargs):
        """Create a mailing list on this domain"""
        fqdn_listname = u'{0}@{1}'.format(list_name, self.mail_host)
        ml = MailingList(list_name=list_name, mail_host=self.mail_host,\
                domain=self, fqdn_listname=fqdn_listname, **kwargs)
        ml.save()
        return ml

    def __unicode__(self):
        return self.mail_host


class Email(BaseModel):

    object_type='email'
    lookup_field = 'address'
    adaptor = AddressAdaptor
    fields = [('address', 'email'), ]

    address = models.EmailField(unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    verified = models.BooleanField(default=False)
    preferences = models.OneToOneField('EmailPrefs', null=True)

    @property
    def display_name(self):
        return self.user.display_name

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(Email, self).save(*args, **kwargs)
            if self.user and self.user.preferred_email is None:
                self.user.preferred_email = self
                self.user.save()
            # preferences
            self.preferences = EmailPrefs()
            self.preferences.save()
        else:
            super(Email, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.address


class UserManager(BaseUserManager):

    def create_user(self, display_name, email, password):
        if not display_name:
            raise ValueError("No display_name Provided!")
        if not password:
            raise ValueError("No Password Provided!")
        user = self.model(display_name=display_name)
        user.save()
        user.add_email(email)
        user.set_password(password)
        return user

    def create_superuser(self, display_name, email, password):
        user = self.create_user(display_name=display_name, email=email, password=password)
        user.is_admin=True
        user.is_staff=True
        user.is_superuser=True
        user.save(using=self._db)
        return user

    def core(self):
        """User.objects.core() returns all Users from Core"""
        return interface.users


class AbstractUser(BaseModel, AbstractBaseUser, PermissionsMixin):
    class Meta:
        abstract = True

    objects = UserManager()

    display_name = models.CharField(max_length=30, unique=True)
    user_id = models.CharField(max_length=40, default=lambda: str(uuid.uuid1().int))
    created_on = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    preferred_email = models.OneToOneField(Email, null=True,
                                           related_name='%(class)s_preferred')

    preferences = models.OneToOneField('UserPrefs', null=True)
    #TODO peer_expiration_timestamp = models.DateTimeField(null=True)

    USERNAME_FIELD = 'display_name'
    REQUIRED_FIELDS = []

    @property
    def emails(self):
        return self.email_set.all()

    def create_preferred_email(self, address):
        email, created = Email.objects.get_or_create(address=address,
                                                     user=self)
        self.preferred_email = email
        self.save()

    def remove_preferred_email(self):
        """
        Remove an Email as the "preferred" email but don't
        delete it. It will still be available in the user's
        email_set.
        """
        self.preferred_email = None
        self.save()

    @property
    def subscriptions(self):
        return Membership.objects.filter(user=self)

    def add_email(self, address):
        email, created = Email.objects.get_or_create(address=address, user=self)
        if created:
            self.email_set.add(email)
            return email
        raise ValueError("Already Exists!")

    def get_email(self, address):
        return self.emails.get(address=address)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=['password'])
        return check_password(raw_password, self.password, setter)

    def __unicode__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if self.pk is None:
                super(AbstractUser, self).save(*args, **kwargs)
                self.preferences = UserPrefs()
                self.preferences.save()
        else:
            super(AbstractUser, self).save(*args, **kwargs)

# AbstractRemotelyBackedObject
class User(AbstractUser):
    fields = [('display_name', 'display_name'), ('email', 'email'),
            ('password', 'password')]
    object_type = 'user'
    lookup_field = 'address'
    adaptor = UserAdaptor


class BasePrefs(BaseModel, AbstractRemotelyBackedObject):

    class Meta:
        abstract = True

    acknowledge_posts = models.NullBooleanField()
    delivery_mode = models.CharField(max_length=50, blank=True)
    delivery_status = models.CharField(max_length=50, blank=True)
    hide_address = models.NullBooleanField()
    preferred_language = models.CharField(max_length=50, blank=True)
    receive_list_copy = models.NullBooleanField()
    receive_own_postings = models.NullBooleanField()

    fields = [('acknowledge_posts', 'acknowledge_posts'),
            ('delivery_status', 'delivery_status'),
            ('delivery_mode', 'delivery_mode'),
            ('hide_address', 'hide_address'),
            ('preferred_language', 'preferred_language'),
            ('receive_list_copy', 'receive_list_copy'),
            ('receive_own_postings', 'receive_own_postings')]

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        setattr(self, key, val)
        self.save()


class UserPrefs(BasePrefs):
    object_type = 'userprefs'
    adaptor = PreferencesAdaptor

class EmailPrefs(BasePrefs):
    pass


# Membership Preferences
class MembershipPrefs(BasePrefs):
    """
    Besides being associated with their own Owner/Moderator/Member,
    each preference object is also associated with Membership.
    """
    object_type = 'preferences'
    adaptor = PreferencesAdaptor
    lookup_field = 'address'

    def __unicode__(self):
        return self.membership.address


class Membership(BaseModel, AbstractRemotelyBackedObject):
    """A Membership is created when a User subscribes to a MailingList"""

    object_type = 'membership'
    adaptor = MembershipAdaptor
    lookup_field = 'address'              #TODO: This has to be unique, but for memberships, email isn't.

    fields = [ ('user.display_name', 'user'),
               ('mlist', 'list_id'),
               ('address', 'address'),
               ('role', 'role'),
            ]

    OWNER = 'owner'
    MODERATOR = 'moderator'
    MEMBER = 'member'
    ROLE_CHOICES = (
            (OWNER, 'Owner'),
            (MODERATOR, 'Moderator'),
            (MEMBER, 'Member')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    mlist = models.ForeignKey(MailingList, null=True)
    address = models.EmailField()         #TODO: This should be associated with Email, but that's too many relations atm. *Sigh*
    preferences = models.OneToOneField(MembershipPrefs, null=True)

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=MEMBER)

    def is_owner(self):
        return self.role == self.OWNER

    def is_moderator(self):
        return self.role == self.MODERATOR

    def is_member(self):
        return self.role == self.MEMBER

    def unsubscribe(self):
        """Unsubscribe from this list"""
        self.delete()

    @property
    def fqdn_listname(self):
        return self.mlist.fqdn_listname

    def save(self, *args, **kwargs):
        """Save a membership and its preferences."""
        if self.pk is None:
            super(Membership, self).save(*args, **kwargs)
            self.preferences = MembershipPrefs()
            self.preferences.save()
            super(Membership, self).save(*args, **kwargs)
        else:
            super(Membership, self).save(*args, **kwargs)

    def __unicode__(self):
        return '{0} on {1}'.format(self.address, self.mlist.fqdn_listname)
