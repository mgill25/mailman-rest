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

    admin_immed_notify = models.BooleanField()
    admin_notify_mchanges = models.BooleanField()
    archive_policy = models.CharField(max_length=50)
    administrivia = models.BooleanField()
    advertised = models.BooleanField()
    allow_list_posts = models.BooleanField()
    anonymous_list = models.BooleanField()
    autorespond_owner = models.CharField(max_length=50, blank=True)
    autoresponse_owner_text = models.TextField(blank=True)
    autorespond_postings = models.CharField(max_length=50, blank=True)
    autoresponse_postings_text = models.TextField(blank=True)
    autorespond_requests = models.CharField(max_length=50, blank=True)
    autoresponse_request_text = models.TextField(blank=True)
    collapse_alternatives = models.BooleanField()
    convert_html_to_plaintext = models.BooleanField()
    filter_content = models.BooleanField()
    first_strip_reply_to = models.BooleanField()
    include_rfc2369_headers = models.BooleanField()
    reply_goes_to_list = models.CharField(max_length=50)
    send_welcome_message = models.BooleanField()

class ListOperationParamMixin(BaseListParamSet):
    """Values controlling the immediate operations of the list"""
    class Meta:
        abstract = True
    # acceptable_aliases - FieldType?
    # autoresponse_grace_period -  Timedelta

    bounces_address = models.EmailField()
    default_member_action = models.CharField(max_length=50)
    default_nonmember_action = models.CharField(max_length=50)
    description = models.CharField(max_length=100, blank=True)
    digest_size_threshold = models.FloatField()
    http_etag = models.CharField(max_length=50)
    join_address = models.EmailField()
    leave_address = models.EmailField()
    next_digest_number = models.IntegerField()
    no_reply_address = models.EmailField()
    owner_address = models.EmailField()
    post_id = models.IntegerField()
    posting_address = models.EmailField()
    posting_pipeline = models.CharField(max_length=50)
    reply_to_address = models.EmailField()
    request_address = models.EmailField()
    scheme = models.CharField(max_length=50)
    volume = models.IntegerField()
    subject_prefix = models.CharField(max_length=50, blank=True)
    web_host = models.CharField(max_length=50)
    welcome_message_uri = models.CharField(max_length=50, blank=True)


class ListParametersMixin(ListConfigParamMixin, ListPolicyParamMixin, ListOperationParamMixin):
    last_post_at = models.DateTimeField(null=True)
    digest_last_sent_at = models.DateTimeField(null=True)

    class Meta:
        abstract = True

class AbstractBaseList(BaseModel):
    created_at = models.DateTimeField(default=timezone.now())

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
            help_text=_("Fully qualified name of the list. It is comprised of list_name + '@' + mail_host"))
    display_name = models.CharField(max_length=100,
            help_text=_("Human readable name for the mailing list"))


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

