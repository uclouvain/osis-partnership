from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from partnership.utils import user_is_adri, user_is_in_user_faculty

__all__ = ['PartnerEntity']


class PartnerEntity(models.Model):
    """
    Une entité d'un partenaire.
    Il peut y avoir plusieurs entités par partenaire.
    """
    partner = models.ForeignKey(
        'partnership.Partner',
        verbose_name=_('partner'),
        on_delete=models.CASCADE,
        related_name='entities',
    )
    name = models.CharField(_('Name'), max_length=255)
    address = models.ForeignKey(
        'partnership.Address',
        verbose_name=_('address'),
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
    )
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
    parent = models.ForeignKey(
        'self',
        verbose_name=_('parent_entity'),
        on_delete=models.PROTECT,
        related_name='childs',
        blank=True,
        null=True,
    )
    comment = models.TextField(_('comment'), default='', blank=True)
    created = models.DateField(_('created'), auto_now_add=True, editable=False)
    modified = models.DateField(_('modified'), auto_now=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '{0}#partner-entity-{1}'.format(
            reverse('partnerships:partners:detail', kwargs={'pk': self.partner_id}),
            self.id,
        )

    def user_can_change(self, user):
        return user_is_adri(user) or user_is_in_user_faculty(user, self.author)

    def user_can_delete(self, user):
        return self.user_can_change(user) and not self.partnerships.exists() and not self.childs.exists()
