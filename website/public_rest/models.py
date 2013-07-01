import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class BaseModel(models.Model):
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
        return self.get(**kwargs)

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

    # acceptable_aliases - FieldType?
    # autoresponse_grace_period -  Timedelta
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


class ListParametersMixin(ListConfigParamMixin, ListPolicyParamMixin, ListOperationParamMixin):
    last_post_at = models.DateTimeField(null=True, default=None)
    digest_last_sent_at = models.DateTimeField(null=True, default=None)

    class Meta:
        abstract = True


class ListSettings(ListParametersMixin):

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        setattr(self, key, val)
        self.save()


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
    settings = models.OneToOneField(ListSettings)

    def save(self, *args, **kwargs):
        """Populate these settings for the current MailingList instance."""
        if self.pk is None:
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
            self.settings.mail_host = self.mail_host
            self.settings.display_name = self.display_name
            self.settings.save()    #XXX: If we need different args for settings and lists?
        super(CoreListMixin, self).save(*args, **kwargs)


class LocalListMixin(models.Model):
    """Fields that are added by us, locally."""
    class Meta:
        abstract = True


class AbstractMailingList(AbstractBaseList, CoreListMixin, LocalListMixin):
    objects = ListManager()

    class Meta:
        abstract = True

    def defer_message(self, request_id):
        pass

    def get_subscribers(self):
        return Subscriber.objects.filter(_list=self)

    def subscribe(self, address, role='member'):
        # Check if the address belongs to a user
        try:
            u = User.objects.get(email__address=address)
        except User.DoesNotExist as e:
            # The user does not exist, create one, using email as the display_name
            u = User(display_name=address)
            u.save()
            e = Email(address=address, user=u)
            e.save()
        # Make a subscription relationship
        s = Subscriber(user=u, _list=self, address=address, role=role)
        s.save()

    def unsubscribe(self, address):
        s = Subscriber.objects.get(_list=self, address=address)
        s.delete()

    def add_owner(self, address):
        self.subscribe(address, role='owner')

    def add_moderator(self, address):
        self.subscribe(address, role='moderator')

    def add_member(self, address):
        self.subscribe(address, role='member')

    @property
    def owners(self):
        return Subscriber.objects.filter(_list=self, role='owner')

    @property
    def moderators(self):
        return Subscriber.objects.filter(_list=self, role='moderator')

    @property
    def members(self):
        return Subscriber.objects.filter(_list=self, role='member')

    @property
    def all_subscribers(self):
        return Subscriber.objects.filter(_list=self)

    def get_member(self, address):
        return Subscriber.objects.get(_list=self, address=address)

class MailingList(AbstractMailingList):
    class Meta:
        swappable = 'MAILINGLIST_MODEL'


# Domain
class DomainManager(models.Manager):
    def get_or_404(self, **kwargs):
        return self.get(**kwargs)


class Domain(BaseModel):

    objects = DomainManager()

    base_url = models.URLField()
    mail_host = models.CharField(max_length=100)
    description = models.TextField()
    contact_address = models.EmailField()

    @property
    def lists(self):
        return MailingList.objects.filter(domain=self)

    def create_list(self, list_name, **kwargs):
        """Create a mailing list on this domain"""
        # A list can't be created without a settings object
        settings = ListSettings()
        settings.save()
        ml = MailingList(list_name=list_name, mail_host=self.mail_host,\
                domain=self, settings=settings, **kwargs)
        ml.save()
        return ml

    def __unicode__(self):
        return self.mail_host


class Email(models.Model):
    address = models.EmailField(unique=True)
    user = models.ForeignKey('User')
    preferred = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)

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

class AbstractUser(AbstractBaseUser, PermissionsMixin):
    class Meta:
        abstract = True

    objects = UserManager()

    display_name = models.CharField(max_length=30, unique=True)
    user_id = models.CharField(max_length=40, default=str(uuid.uuid1().int))      # BitIntegerField causes overflow
    created_on = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'display_name'
    REQUIRED_FIELDS = []


    @property
    def emails(self):
        return self.email_set.all()

    @property
    def subscriptions(self):
        return Subscriber.objects.filter(user=self)

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


class User(AbstractUser):
    pass

# Subscriber Preferences
class BaseSubscriberPrefs(BaseModel):
    class Meta:
        abstract = True

    acknowledge_posts = models.NullBooleanField()
    delivery_mode = models.CharField(max_length=50, blank=True)
    delivery_status = models.CharField(max_length=50, blank=True)
    hide_address = models.NullBooleanField()
    preferred_language = models.CharField(max_length=50, blank=True)
    receive_list_copy = models.NullBooleanField()
    receive_own_postings = models.NullBooleanField()
    subscriber = models.OneToOneField('Subscriber')

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        setattr(self, key, val)
        self.save()


class OwnerPrefs(BaseSubscriberPrefs):
    pass


class ModeratorPrefs(BaseSubscriberPrefs):
    pass


class MemberPrefs(BaseSubscriberPrefs):
    pass


#TODO: Think of a better name than Subscribers
class Subscriber(BaseModel):
    """A Member is created when a User subscribes to a MailingList"""
    OWNER = 'owner'
    MODERATOR = 'moderator'
    MEMBER = 'member'
    ROLE_CHOICES = (
            (OWNER, 'Owner'),
            (MODERATOR, 'Moderator'),
            (MEMBER, 'Member')
    )
    user = models.ForeignKey(User)
    _list = models.ForeignKey(MailingList)
    address = models.EmailField()
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

    def save(self, *args, **kwargs):
        if self.pk is None:
            # First save this object
            super(Subscriber, self).save(*args, **kwargs)
            # Then save the preferences
            if self.role == self.MEMBER:
                prefs = MemberPrefs(subscriber=self)
            elif self.role == self.MODERATOR:
                prefs = ModeratorPrefs(subscriber=self)
            elif self.role == self.OWNER:
                prefs = OwnerPrefs(subscriber=self)
            prefs.save()
        else:
            super(Subscriber, self).save(*args, **kwargs)

    @property
    def preferences(self):
        if self.role == self.OWNER:
            return self.ownerprefs
        elif self.role == self.MODERATOR:
            return self.moderatorprefs
        elif self.role == self.MEMBER:
            return self.memberprefs

    def __unicode__(self):
        return '{0} on {1}'.format(self.address, self._list.fqdn_listname)
