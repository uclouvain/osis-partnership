from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from partnership.models import MediaVisibility

__all__ = [
    'Media',
    'MediaType',
]


class MediaType(models.Model):
    """
    Type de média configurable dans l'administration Django.
    """
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
    """
    Un fichier uploadé ou un lien.
    """
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
        choices=MediaVisibility.choices(),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
    )

    def __str__(self):
        return self.name

    def get_document_file_type(self):
        return self.file.name.split('.')[-1]

    def get_document_file_size(self):
        return self.file.size
