import uuid
from datetime import date

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

__all__ = [
    'Partner',
    'PartnerTag',
    'PartnerType',
]


class PartnerType(models.Model):
    """
    Le type de partenaire

    Dans un autre modèle car configurable dans l'administration Django.
    """
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class PartnerTag(models.Model):
    """
    Tags décrivant un partenaire.

    Dans un autre modèle car configurable dans l'administration Django et
    possibilité d'en mettre plusieurs par partenaire.
    """
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class Partner(models.Model):
    """
    Le modèle principal représentant un partenaire.
    """
    CONTACT_TYPE_CHOICES = (
        ('EPLUS-EDU-HEI', _('Higher education institution (tertiary level)')),
        ('EPLUS-EDU-GEN-PRE', _('School/Institute/Educational centre – General education (pre-primary level)')),
        ('EPLUS-EDU-GEN-PRI', _('School/Institute/Educational centre – General education (primary level)')),
        ('EPLUS-EDU-GEN-SEC', _('School/Institute/Educational centre – General education (secondary level)')),
        ('EPLUS-EDU-VOC-SEC', _('School/Institute/Educational centre – Vocational Training (secondary level)')),
        ('EPLUS-EDU-VOC-TER', _('School/Institute/Educational centre – Vocational Training (tertiary level)')),
        ('EPLUS-EDU-ADULT', _('School/Institute/Educational centre – Adult education')),
        ('EPLUS-BODY-PUB-NAT', _('National Public body')),
        ('EPLUS-BODY-PUB-REG', _('Regional Public body')),
        ('EPLUS-BODY-PUB-LOC', _('Local Public body')),
        ('EPLUS-ENT-SME', _('Small and medium sized enterprise')),
        ('EPLUS-ENT-LARGE', _('Large enterprise')),
        ('EPLUS-NGO', _('Non-governmental organisation/association/social enterprise')),
        ('EPLUS-FOUND', _('Foundation')),
        ('EPLUS-SOCIAL', _('Social partner or other representative of working life '
                           '(chambers of commerce, trade union, trade association)')),
        ('EPLUS-RES', _('Research Institute/Centre')),
        ('EPLUS-YOUTH-COUNCIL', _('National Youth Council')),
        ('EPLUS-ENGO', _('European NGO')),
        ('EPLUS-NET-EU', _('EU-wide network')),
        ('EPLUS-YOUTH-GROUP', _('Group of young people active in youth work')),
        ('EPLUS-EURO-GROUP-COOP', _('European grouping of territorial cooperation')),
        ('EPLUS-BODY-ACCRED', _('Accreditation, _(certification or qualification body')),
        ('EPLUS-BODY-CONS', _('Counsellzing body')),
        ('EPLUS-INTER', _('International organisation under public law')),
        ('EPLUS-SPORT-PARTIAL', _('Organisation or association representing (parts of) the sport sector')),
        ('EPLUS-SPORT-FED', _('Sport federation')),
        ('EPLUS-SPORT-LEAGUE', _('Sport league')),
        ('EPLUS-SPORT-CLUB', _('Sport club')),
        ('OTH', _('Other')),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    external_id = models.CharField(
        _('external_id'),
        help_text=_('to_synchronize_with_epc'),
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        editable=False,
    )
    changed = models.DateField(_('changed'), auto_now=True, editable=False)

    is_valid = models.BooleanField(_('is_valid'), default=False)
    name = models.CharField(_('Name'), max_length=255)
    is_ies = models.BooleanField(_('is_ies'), default=False)
    partner_type = models.ForeignKey(
        PartnerType,
        verbose_name=_('partner_type'),
        related_name='partners',
        on_delete=models.PROTECT,
    )
    partner_code = models.CharField(_('partner_code'), max_length=255, unique=True, null=True, blank=True)
    pic_code = models.CharField(_('pic_code'), max_length=255, unique=True, null=True, blank=True)
    erasmus_code = models.CharField(_('erasmus_code'), max_length=255, unique=True, null=True, blank=True)
    start_date = models.DateField(_('partner_start_date'), null=True, blank=True)
    end_date = models.DateField(_('partner_end_date'), null=True, blank=True)
    now_known_as = models.ForeignKey(
        'self',
        verbose_name=_('now_known_as'),
        on_delete=models.PROTECT,
        related_name='formely_known_as',
        null=True,
        blank=True,
    )

    contact_address = models.ForeignKey(
        'partnership.Address',
        verbose_name=_('address'),
        on_delete=models.PROTECT,
        related_name='partners',
        blank=True,
        null=True,
    )
    website = models.URLField(_('website'))
    email = models.EmailField(
        _('email'),
        help_text=_('mandatory_if_not_pic_ies'),
        null=True,
        blank=True,
    )
    phone = models.CharField(
        _('phone'),
        max_length=255,
        help_text=_('mandatory_if_not_pic_ies'),
        null=True,
        blank=True,
    )
    is_nonprofit = models.NullBooleanField(_('is_nonprofit'), blank=True)
    is_public = models.NullBooleanField(_('is_public'), blank=True)
    contact_type = models.CharField(
        _('partner_contact_type'),
        max_length=255,
        help_text=_('mandatory_if_not_pic_ies'),
        choices=CONTACT_TYPE_CHOICES,
        null=True,
        blank=True,
    )

    use_egracons = models.BooleanField(_('use_egracons'), default=False)
    comment = models.TextField(_('comment'), default='', blank=True)
    tags = models.ManyToManyField(
        PartnerTag,
        verbose_name=_('tags'),
        related_name='partners',
        blank=True,
    )

    medias = models.ManyToManyField(
        'partnership.Media',
        verbose_name=_('medias'),
        related_name='+',
        blank=True,
    )

    created = models.DateField(_('created'), auto_now_add=True, editable=False)
    author = models.ForeignKey(
        'base.Person',
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        null=True,
    )

    class Meta:
        ordering = ('-created',)
        permissions = (
            ('can_access_partners', _('can_access_partners')),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('partnerships:partners:detail', kwargs={'pk': self.pk})

    @property
    def is_actif(self):
        """ Partner is not actif if it has date and is not within those. """
        if self.start_date is not None and date.today() < self.start_date:
            return False
        if self.end_date is not None and date.today() > self.end_date:
            return False
        return True

    @property
    def agreements(self):
        from ..partnership.agreement import PartnershipAgreement
        return (
            PartnershipAgreement.objects
            .select_related('partnership', 'start_academic_year', 'end_academic_year')
            .filter(partnership__partner=self)
        )