import uuid
from datetime import date, datetime

from django.db import models
from django.db.models import Prefetch, Subquery, OuterRef, Q
from django.db.models.functions import Now
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.entity_version_address import EntityVersionAddress
from base.models.organization import Organization

__all__ = [
    'Partner',
    'PartnerTag',
]


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


class PartnerQueryset(models.QuerySet):
    def annotate_dates(self, filter_value=None):
        qs = self.annotate(
            start_date=Subquery(EntityVersion.objects.filter(
                entity__organization=OuterRef('organization_id'),
                parent__isnull=True,
            ).order_by('start_date').values('start_date')[:1]),
            end_date=Subquery(EntityVersion.objects.filter(
                entity__organization=OuterRef('organization_id'),
                parent__isnull=True,
            ).order_by('-start_date').values('end_date')[:1]),
        )
        if filter_value:
            return qs.filter(
                (Q(start_date__isnull=True) | Q(start_date__lte=Now()))
                & (Q(end_date__isnull=True) | Q(end_date__gte=Now()))
            )
        elif filter_value is not None:
            return qs.filter(
                Q(start_date__gt=Now()) | Q(end_date__lt=Now())
            )
        return qs

    def annotate_website(self, of_datetime=None):
        if not of_datetime:
            of_datetime = datetime.now()
        return self.annotate(
            website=Subquery(EntityVersion.objects.current(of_datetime).filter(
                entity__organization=OuterRef('organization_id'),
                parent__isnull=True,
            ).order_by('-start_date').values('entity__website')[:1]),
        )

    def annotate_address(self, *fields):
        """
        Add annotations on contact address

        :param fields: list of fields relative to EntityVersionAddress
            If a field contains a traversal, e.g. country__name, it will be
            available as country_name
        """
        contact_address_qs = EntityVersion.objects.filter(
            entity__organization=OuterRef('organization'),
            parent__isnull=True,
        ).order_by('-start_date')
        qs = self
        for field in fields:
            lookup = Subquery(contact_address_qs.values(
                'entityversionaddress__{}'.format(field)
            )[:1])
            qs = qs.annotate(**{field.replace('__', '_'): lookup})
        return qs

    def prefetch_address(self):
        return self.prefetch_related(
            # We need to do this nested prefetch because every level has a
            # particular query
            Prefetch(
                'organization__entity_set',
                Entity.objects.filter(
                    entityversion__parent__isnull=True,
                ).prefetch_related(Prefetch(
                    'entityversion_set',
                    EntityVersion.objects.filter(
                        parent__isnull=True,
                    ).order_by('-start_date').prefetch_related(Prefetch(
                        'entityversionaddress_set',
                        EntityVersionAddress.objects.select_related(
                            'country__continent'
                        ),
                        to_attr='address'
                    )),
                    to_attr='versions',
                )),
                to_attr='entities',
            ),

        )


class PartnerManager(models.manager.BaseManager.from_queryset(PartnerQueryset)):
    def get_queryset(self):
        return super().get_queryset().select_related('organization')


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

    organization = models.OneToOneField(
        Organization,
        on_delete=models.PROTECT,
    )

    changed = models.DateField(_('changed'), auto_now=True, editable=False)

    is_valid = models.BooleanField(_('is_valid'), default=False)
    is_ies = models.BooleanField(_('is_ies'), default=False)
    pic_code = models.CharField(_('pic_code'), max_length=255, unique=True, null=True, blank=True)
    erasmus_code = models.CharField(_('erasmus_code'), max_length=255, unique=True, null=True, blank=True)

    now_known_as = models.ForeignKey(
        'self',
        verbose_name=_('now_known_as'),
        on_delete=models.PROTECT,
        related_name='formely_known_as',
        null=True,
        blank=True,
    )

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

    objects = PartnerManager()

    class Meta:
        ordering = ('-created',)
        permissions = (
            ('can_access_partners', _('can_access_partners')),
        )

    def __str__(self):
        return self.organization.name

    def get_absolute_url(self):
        return reverse('partnerships:partners:detail', kwargs={'pk': self.pk})

    @cached_property
    def is_actif(self):
        """ Partner is not active if it has date and is not within those. """
        start_date = self.start_date if hasattr(self, 'start_date') else self.organization.start_date
        end_date = self.end_date if hasattr(self, 'end_date') else self.organization.end_date
        if start_date is not None and date.today() < start_date:
            return False
        if end_date is not None and date.today() > end_date:
            return False
        return True

    @cached_property
    def agreements(self):
        from ..partnership.agreement import PartnershipAgreement
        from ..partnership.partnership import Partnership
        return (
            PartnershipAgreement.objects
            .filter(partnership__partner=self)
            .select_related('start_academic_year', 'end_academic_year')
            .prefetch_related(
                'media',
                Prefetch(
                    'partnership',
                    queryset=Partnership.objects.add_acronyms()
                ),
            )
        )

    @cached_property
    def contact_address(self):
        if not hasattr(self, '_prefetched_objects_cache'):
            return EntityVersionAddress.objects.filter(
                entity_version__entity__organization_id=self.organization_id,
                entity_version__parent__isnull=True,
            ).order_by('-entity_version__start_date').first()
        # We surely have a entity and a version, but we may not have an address
        address = self.organization.entities[0].versions[0].address
        if address:
            return address[0]
