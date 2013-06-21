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

    def save(self, *args, **kwargs):
        if self.pk is None:             # New Record.
            if not self.join_address:
                self.join_address = u'{0}-join@{1}'.format(self.list_name, self.mail_host)
            if not self.bounces_address:
                self.bounces_address = u'{0}-bounces@{1}'.format(self.list_name, self.mail_host)
            if not self.leave_address:
                self.leave_address = u'{0}-leave@{1}'.format(self.list_name, self.mail_host)
            if not self.no_reply_address:
                self.no_reply_address = u'noreply@{0}'.format(self.mail_host)
            if not self.owner_address:
                self.owner_address = u'{0}-owner@{1}'.format(self.list_name, self.mail_host)
            if not self.fqdn_listname:
                self.fqdn_listname = u'{0}@{1}'.format(self.list_name, self.mail_host)
            if not self.request_address:
                self.request_address = u'{0}-request@{1}'.format(self.list_name, self.mail_host)
        super(ListOperationParamMixin, self).save(*args, **kwargs)


class ListParametersMixin(ListConfigParamMixin, ListPolicyParamMixin, ListOperationParamMixin):
    last_post_at = models.DateTimeField(null=True, default=None)
    digest_last_sent_at = models.DateTimeField(null=True, default=None)

    class Meta:
        abstract = True

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

    # Temporary Attributes that will be relationships in the future
    owners = []
    moderators = []

    def defer_message(self, request_id):
        pass


class LocalListMixin(models.Model):
    """Fields that are added by us, locally."""
    class Meta:
        abstract = True


class AbstractMailingList(AbstractBaseList, CoreListMixin, LocalListMixin, ListParametersMixin):
    objects = ListManager()

    class Meta:
        abstract = True

class MailingList(AbstractMailingList):
    class Meta:
        swappable = 'MAILINGLIST_MODEL'


# Domain
class DomainManager(models.Manager):
    def get_or_404(self, **kwargs):
        return self.get(**kwargs)

class Domain(models.Model):

    objects = DomainManager()

    base_url = models.URLField()
    mail_host = models.CharField(max_length=100)
    description = models.TextField()
    contact_address = models.EmailField()


    @property
    def lists(self):
        return MailingList.objects.filter(domain=self)

    def create_list(self, list_name):
        """Create a mailing list on this domain"""
        ml = MailingList(list_name=list_name, mail_host=self.mail_host, domain=self)
        ml.save()
        return ml

