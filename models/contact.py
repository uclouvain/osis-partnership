from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from .enums import ContactTitle

__all__ = [
    'Contact',
    'ContactType',
]


class ContactType(models.Model):
    """
    Type de contact configurable dans l'administration Django.
    """
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class Contact(models.Model):
    """
    Une personne avec téléphone / email / etc.
    """
    type = models.ForeignKey(
        ContactType,
        verbose_name=_('contact_type'),
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )
    title = models.CharField(
        _('contact_title'),
        max_length=50,
        choices=ContactTitle.choices(),
        null=True,
        blank=True,
    )
    last_name = models.CharField(
        _('last_name'),
        max_length=255,
        blank=True,
        null=True,
    )
    first_name = models.CharField(
        _('first_name'),
        max_length=255,
        blank=True,
        null=True,
    )
    society = models.CharField(
        _('society'),
        max_length=255,
        blank=True,
        null=True,
    )
    function = models.CharField(
        _('function'),
        max_length=255,
        blank=True,
        null=True,
    )
    phone = models.CharField(
        _('phone'),
        max_length=255,
        blank=True,
        null=True,
    )
    mobile_phone = models.CharField(
        _('mobile_phone'),
        max_length=255,
        blank=True,
        null=True,
    )
    fax = models.CharField(
        _('fax'),
        max_length=255,
        blank=True,
        null=True,
    )
    email = models.EmailField(
        pgettext_lazy('partnership', 'email'),
        blank=True,
        null=True,
    )
    comment = models.TextField(
        _('comment'),
        default='',
        blank=True,
    )

    def __str__(self):
        chunks = []
        if self.title is not None:
            chunks.append(self.get_title_display())
        if self.last_name:
            chunks.append(self.last_name)
        if self.first_name:
            chunks.append(self.first_name)
        return ' '.join(chunks)

    @property
    def is_empty(self):
        return not any([
            self.type,
            self.title,
            self.last_name,
            self.first_name,
            self.society,
            self.function,
            self.phone,
            self.mobile_phone,
            self.fax,
            self.email,
            self.comment,
        ])
