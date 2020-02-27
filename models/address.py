from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = ['Address']


class Address(models.Model):
    """
    Une adresse postale.
    """
    name = models.CharField(
        _('Name'),
        help_text=_('address_name_help_text'),
        max_length=255,
        blank=True,
        null=True
    )
    address = models.TextField(
        _('address'),
        default='',
        blank=True,
    )
    postal_code = models.CharField(
        _('postal_code'),
        max_length=20,
        blank=True,
        null=True,
    )
    city = models.CharField(
        _('city'),
        max_length=255,
        blank=True,
        null=True,
    )
    city_french = models.CharField(
        _('city_french'),
        max_length=255,
        blank=True,
        null=True,
    )
    city_english = models.CharField(
        _('city_english'),
        max_length=255,
        blank=True,
        null=True,
    )
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_('country'),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.one_line_display()

    def one_line_display(self):
        components = []
        if self.name:
            components.append(self.name)
        if self.address:
            components.append(self.address)
        if self.postal_code:
            components.append(self.postal_code)
        if self.city:
            components.append(self.city)
        if self.country:
            components.append(str(self.country).upper())
        return ', '.join(components)
