from django.db import models
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

__all__ = ['PartnerEntity']


class PartnerEntity(models.Model):
    """
    Une entité d'un partenaire.
    Il peut y avoir plusieurs entités par partenaire.
    """
    entity_version = models.OneToOneField(
        'base.EntityVersion',
        verbose_name=_('partner'),
        on_delete=models.PROTECT,
    )
    name = models.CharField(_('Name'), max_length=255)
    contact_in = models.ForeignKey(
        'partnership.Contact',
        verbose_name=_('contact_in'),
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
    )
    contact_out = models.ForeignKey(
        'partnership.Contact',
        verbose_name=_('contact_out'),
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
    )
    comment = models.TextField(_('comment'), default='', blank=True)
    created = models.DateField(_('created'), auto_now_add=True, editable=False)
    modified = models.DateField(_('modified'), auto_now=True, editable=False)
    author = models.ForeignKey(
        'base.Person',
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        null=True,
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '{0}#partner-entity-{1}'.format(
            resolve_url('partnerships:partners:detail', pk=self.partner.pk),
            self.id,
        )

    @cached_property
    def partner(self):
        return self.entity_version.entity.organization.partner

    @cached_property
    def parent_entity(self):
        return self.entity_version.parent.most_recent_entity_version.partnerentity
