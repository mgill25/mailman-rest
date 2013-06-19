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
        print("Creating a List")
        lst = self.model(created_at=now, list_name=list_name, mail_host=mail_host,
                fqdn_listname=fqdn_listname, **extra_fields)
        lst.save()
        return lst


class AbstractBaseList(BaseModel):
    created_at = models.DateTimeField(default=timezone.now())

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.list_name


class CoreListMixin(models.Model):
    """Fields that are part of the Mailman core."""
    list_name = models.CharField(max_length=100)        # TODO: Verify properties like max-length from MM-core
    mail_host = models.CharField(max_length=100,
            help_text=_("Domain Name hosting this mailing list"))
    fqdn_listname = models.CharField(max_length=100,
            help_text=_("Fully qualified name of the list. It is comprised of list_name + '@' + mail_host"))

    class Meta:
        abstract = True


class LocalListMixin(models.Model):
    """Fields that are added by us, locally."""
    class Meta:
        abstract = True


class AbstractMailingList(AbstractBaseList, CoreListMixin, LocalListMixin):

    objects = ListManager()

    class Meta:
        abstract = True


class MailingList(AbstractMailingList):
    class Meta:
        swappable = 'MAILINGLIST_MODEL'
