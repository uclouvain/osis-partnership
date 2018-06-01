from datetime import date

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class PartnerType(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class PartnerTag(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class Partner(models.Model):
    external_id = models.CharField(max_length=255, unique=True)
    is_valid = models.BooleanField(_('is_valid'), default=False)
    name = models.CharField(_('name'), max_length=255)
    is_ies = models.BooleanField(_('is_ies'), default=False)
    partner_type = models.ForeignKey(
        PartnerType,
        verbose_name=_('partner_type'),
        related_name='partners',
        on_delete=models.PROTECT,
    )
    partner_code = models.CharField(_('partner_code'), max_length=255, unique=True)
    pic_code = models.CharField(_('pic_code'), max_length=255, unique=True)
    erasmus_code = models.CharField(_('erasmus_code'), max_length=255, unique=True)
    start_date = models.DateField(_('start_date'), null=True, blank=True)
    end_date = models.DateField(_('end_date'), null=True, blank=True)
    now_known_as = models.ForeignKey(
        'self',
        verbose_name=_('now_known_as'),
        related_name='formely_known_as',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # contact_address = TODO
    website = models.URLField(_('website'))
    email = models.EmailField(_('email'), null=True, blank=True)
    phone = models.CharField(_('phone'), max_length=255, null=True, blank=True)
    is_nonprofit = models.NullBooleanField(_('is_nonprofit'), blank=True)
    is_public = models.NullBooleanField(_('is_public'), blank=True)
    contact_type = models.CharField(_('organisation_type'), max_length=255, null=True, blank=True)

    use_egracons = models.BooleanField(_('use_egracons'), default=False)
    comment = models.TextField(_('comment'), default='', blank=True)
    tags = models.ManyToManyField(
        PartnerTag,
        verbose_name=_('tags'),
        related_name='partners',
        blank=True,
    )

    # MEDIAS => Modèle déjà existant ?

    created = models.DateField(_('created'), auto_now_add=True, editable=False)
    modified = models.DateField(_('modified'), auto_now=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        editable=False,
    )

    # Entités => model base.Entity ?

    class Meta:
        ordering = ('-created',)
        permissions = (
            ('can_access_partners', _('can_access_partners')),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('partnerships:partner_detail', kwargs={'pk': self.pk})

    @property
    def is_actif(self):
        """ Partner is not actif if it has date and is not within those. """
        if self.start_date is not None and date.today() < self.start_date:
            return False
        if self.end_date is not None and date.today() > self.end_date:
            return False
        return True


class PartnershipType(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class PartnershipTag(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class Partnership(models.Model):
    MOBILITY_TYPE_CHOICES = (
        ('SMS', _('mobility_type_sms')),
        ('SMP', _('mobility_type_smp')),
        ('STA', _('mobility_type_sta')),
        ('STT', _('mobility_type_stt')),
        ('NA', _('mobility_type_na')),
    )

    external_id = models.CharField(max_length=255, unique=True)
    is_valid = models.BooleanField(_('is_valid'), default=False)
    partner = models.ForeignKey(
        Partner,
        verbose_name=_('partner'),
        related_name='partnerships',
        on_delete=models.PROTECT,
    )
    # partner_entity = ?
    # university => entity
    # university_labo => entity
    # university_offers = ?
    # supervisor = ?

    start_date = models.DateField(_('start_date'), null=True, blank=True)
    end_date = models.DateField(_('end_date'), null=True, blank=True)

    # domaine etudes ?
    # niveaux etude ?
    mobility_type = models.CharField(_('mobility_type'), max_length=255, choices=MOBILITY_TYPE_CHOICES)
    partner_type = models.ForeignKey(
        PartnershipType,
        verbose_name=_('partnership_type'),
        related_name='partnerships',
        on_delete=models.PROTECT,
    )

    # Accord signé ?
    # Contacts ?

    comment = models.TextField(_('comment'), default='', blank=True)
    tags = models.ManyToManyField(
        PartnershipTag,
        verbose_name=_('tags'),
        related_name='partnerships',
        blank=True,
    )

    created = models.DateField(_('created'), auto_now_add=True, editable=False)
    modified = models.DateField(_('modified'), auto_now=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        editable=False,
    )

    class Meta:
        ordering = ('-created',)
        permissions = (
            ('can_access_partners', _('can_access_partnerships')),
        )

    def __str__(self):
        return _('partnership_with_{partner}').format(self.partner)