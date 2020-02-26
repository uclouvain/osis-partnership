from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = [
    'Media',
    'MediaType',
]


class MediaType(models.Model):
    SUMMARY_TABLE = 'summary-table'

    code = models.CharField(
        _('code'),
        max_length=250,
    )
    label = models.CharField(
        _('label'),
        max_length=250,
    )

    def __str__(self):
        return '{} - {}'.format(self.code, self.label)


class Media(models.Model):
    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_STAFF = 'staff'
    VISIBILITY_STAFF_STUDENT = 'staff_student'
    VISIBILITY_CHOICES = (
        (VISIBILITY_PUBLIC, _('visibility_public')),
        (VISIBILITY_STAFF, _('visibility_staff')),
        (VISIBILITY_STAFF_STUDENT, _('visibility_staff_student')),
    )

    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('description'), default='', blank=True)
    file = models.FileField(
        _('file'),
        help_text=_('media_file_or_url'),
        upload_to='partnerships/',
        blank=True,
        null=True,
    )
    url = models.URLField(
        _('url'),
        help_text=_('media_file_or_url'),
        blank=True,
        null=True,
    )
    type = models.ForeignKey(
        MediaType,
        verbose_name=_('type'),
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    is_visible_in_portal = models.BooleanField(
        _('is_visible_in_portal'),
        default=True,
        blank=True,
    )
    visibility = models.CharField(
        _('visibility'),
        max_length=50,
        choices=VISIBILITY_CHOICES,
    )
    author = models.ForeignKey(
        'base.Person',
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        null=True,
    )

    def __str__(self):
        return self.name

    def get_document_file_type(self):
        return self.file.name.split('.')[-1]

    def get_document_file_size(self):
        return self.file.size
