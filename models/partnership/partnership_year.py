from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import OuterRef, Subquery
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from base.models.entity_version import EntityVersion
from ..enums.partnership import PartnershipType

__all__ = [
    'PartnershipMission',
    'PartnershipYear',
]


class PartnershipYear(models.Model):
    """
    Données annualisées concernant un partenariat.
    """
    partnership = models.ForeignKey(
        'partnership.Partnership',
        verbose_name=_('partnership'),
        on_delete=models.PROTECT,
        related_name='years',
    )
    academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('academic_year'),
        on_delete=models.PROTECT,
        related_name='+',
    )
    education_fields = models.ManyToManyField(
        'reference.DomainIsced',
        verbose_name=_('partnership_year_education_fields'),
        blank=False,
    )
    education_levels = models.ManyToManyField(
        'partnership.PartnershipYearEducationLevel',
        verbose_name=_('partnership_year_education_levels'),
        related_name='partnerships_years',
        blank=True,
    )
    entities = models.ManyToManyField(
        'base.Entity',
        verbose_name=_('partnership_year_entities'),
        help_text=_('partnership_year_entities_help_text'),
        related_name='partnerships_years',
        blank=True,
    )
    offers = models.ManyToManyField(
        'base.EducationGroupYear',
        verbose_name=_('partnership_year_offers'),
        help_text=_('partnership_year_offers_help_text'),
        related_name='partnerships',
        blank=True,
    )
    is_sms = models.BooleanField(_('is_sms'), default=False, blank=True)
    is_smp = models.BooleanField(_('is_smp'), default=False, blank=True)
    is_smst = models.BooleanField(_('is_smst'), default=False, blank=True)
    is_sta = models.BooleanField(_('is_sta'), default=False, blank=True)
    is_stt = models.BooleanField(_('is_stt'), default=False, blank=True)
    eligible = models.BooleanField(
        _('eligible'),
        default=True,
        blank=True,
    )
    funding_type = models.ForeignKey(
        'partnership.FundingType',
        verbose_name=_('funding_type'),
        on_delete=models.PROTECT,
        related_name='years',
        null=True,
    )
    missions = models.ManyToManyField('partnership.PartnershipMission')

    class Meta:
        unique_together = ('partnership', 'academic_year')
        ordering = ('academic_year__year',)
        verbose_name = _('partnership_year')

    def __str__(self):
        return _('partnership_year_{partnership}_{year}').format(
            partnership=self.partnership,
            year=self.academic_year,
        )

    @property
    def has_sm(self):
        return self.is_sms or self.is_smp

    @cached_property
    def is_valid(self):
        ranges = self.partnership.valid_agreements_dates_ranges
        for range in ranges:
            if (self.academic_year.start_date.year >= range['start']
                    and self.academic_year.end_date.year <= range['end'] + 1):
                return True
        return False

    @cached_property
    def planned_activity(self):
        activities = []
        if self.is_sms:
            activities.append('SMS')
        if self.is_smp:
            activities.append('SMP')
        if self.is_sta:
            activities.append('STA')
        if self.is_stt:
            activities.append('STT')
        return ', '.join(activities)

    def get_entities_with_titles(self):
        return self.entities.annotate(
            most_recent_acronym=Subquery(
                EntityVersion.objects
                    .filter(entity=OuterRef('pk'))
                    .order_by('-start_date')
                    .values('acronym')[:1]
            ),
            most_recent_title=Subquery(
                EntityVersion.objects
                    .filter(entity=OuterRef('pk'))
                    .order_by('-start_date')
                    .values('title')[:1]
            ),
        )

    def get_financing(self):
        if not self.eligible:
            return None
        country = self.partnership.partner.contact_address.country
        if country is None:
            return None
        from ..financing import Financing
        return (
            Financing.objects
            .select_related('academic_year')
            .filter(
                countries=country,
                academic_year=self.academic_year,
            ).first()
        )


class PartnershipMission(models.Model):
    label = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True)
    types = ArrayField(
        models.CharField(max_length=50, choices=PartnershipType.choices()),
    )

    class Meta:
        verbose_name = _('partnership_mission')

    def __str__(self):
        return "{} - {}".format(self.code, self.label)
