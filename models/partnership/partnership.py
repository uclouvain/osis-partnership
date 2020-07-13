import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, Min
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY, SECTOR
from base.utils.cte import CTESubquery
from partnership.models import AgreementStatus, PartnershipType
from partnership.utils import merge_agreement_ranges

__all__ = [
    'Partnership',
    'PartnershipTag',
]


class PartnershipTag(models.Model):
    """
    Tags décrivant un partenariat.

    Dans un autre modèle car configurable dans l'administration Django et
    possibilité d'en mettre plusieurs par partenariat.
    """
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class PartnershipQuerySet(models.QuerySet):
    def add_acronyms(self):
        ref = models.OuterRef('ucl_entity__pk')

        cte = EntityVersion.objects.with_children(entity_id=ref)
        qs = cte.join(
            EntityVersion, id=cte.col.id
        ).with_cte(cte).order_by('-start_date')

        last_version = EntityVersion.objects.filter(
            entity=ref
        ).order_by('-start_date')

        return self.annotate(
            ucl_sector_most_recent_acronym=CTESubquery(
                qs.filter(entity_type=SECTOR).values('acronym')[:1]
            ),
            ucl_sector_most_recent_title=CTESubquery(
                qs.filter(entity_type=SECTOR).values('title')[:1]
            ),
            ucl_faculty_most_recent_acronym=CTESubquery(
                qs.filter(
                    entity_type=FACULTY,
                ).exclude(
                    entity_id=ref,
                ).values('acronym')[:1]
            ),
            ucl_faculty_most_recent_title=CTESubquery(
                qs.filter(
                    entity_type=FACULTY,
                ).exclude(
                    entity_id=ref,
                ).values('title')[:1]
            ),
            ucl_entity_most_recent_acronym=CTESubquery(
                last_version.values('acronym')[:1]
            ),
            ucl_entity_most_recent_title=CTESubquery(
                last_version.values('title')[:1]
            ),
        )


class Partnership(models.Model):
    """
    Le modèle principal représentant un partenariat.
    """
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    partnership_type = models.CharField(
        _('partnership_type'),
        max_length=255,
        choices=PartnershipType.choices(),
    )

    external_id = models.CharField(
        _('external_id'),
        help_text=_('to_synchronize_with_epc'),
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        editable=False,
    )

    partner = models.ForeignKey(
        'partnership.Partner',
        verbose_name=_('partner'),
        on_delete=models.PROTECT,
        related_name='partnerships',
    )
    partner_entity = models.ForeignKey(
        'partnership.PartnerEntity',
        verbose_name=_('partner_entity'),
        on_delete=models.PROTECT,
        related_name='partnerships',
        blank=True,
        null=True,
    )
    ucl_entity = models.ForeignKey(
        'base.Entity',
        verbose_name=_('ucl_entity'),
        on_delete=models.PROTECT,
        related_name='partnerships',
    )
    supervisor = models.ForeignKey(
        'base.Person',
        verbose_name=_('partnership_supervisor'),
        related_name='partnerships_supervisor',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    contacts = models.ManyToManyField(
        'partnership.Contact',
        verbose_name=_('contacts'),
        related_name='+',
        blank=True,
    )

    medias = models.ManyToManyField(
        'partnership.Media',
        verbose_name=_('medias'),
        related_name='+',
        blank=True,
    )

    comment = models.TextField(
        _('comment'),
        help_text=_('invisible_on_api'),
        default='',
        blank=True,
    )
    tags = models.ManyToManyField(
        'partnership.PartnershipTag',
        verbose_name=_('tags'),
        related_name='partnerships',
        blank=True,
    )

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
    is_public = models.BooleanField(
        verbose_name=_('partnership_is_public'),
        default=True,
        help_text=_('partnership_is_public_help_text'),
    )

    start_date = models.DateField(_('start_date'), null=True)
    end_date = models.DateField(_('end_date'), null=True)

    objects = PartnershipQuerySet.as_manager()

    class Meta:
        ordering = ('-created',)
        permissions = (
            ('can_access_partnerships', _('can_access_partnerships')),
        )

    def __str__(self):
        return _('partnership_with_{partner}').format(partner=self.partner)

    def get_absolute_url(self):
        return reverse('partnerships:detail', kwargs={'pk': self.pk})

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_("End date must be after start date"))

    @cached_property
    def is_valid(self):
        if self.partnership_type == PartnershipType.PROJECT.name:
            return True
        return self.validated_agreements.exists()

    @property
    def validated_agreements(self):
        return self.agreements.filter(status=AgreementStatus.VALIDATED.name)

    @cached_property
    def start_partnership_year(self):
        return self.years.order_by('academic_year__year').first()

    @cached_property
    def end_partnership_year(self):
        return self.years.order_by('academic_year__year').last()

    @cached_property
    def start_academic_year(self):
        partnership_year = self.start_partnership_year
        if partnership_year is None:
            return None
        return partnership_year.academic_year

    @cached_property
    def end_academic_year(self):
        partnership_year = self.end_partnership_year
        if partnership_year is None:
            return None
        return partnership_year.academic_year

    @cached_property
    def valid_start_date(self):
        if not self.validated_agreements.exists():
            return None
        return self.validated_agreements.aggregate(
            start_date=Min('start_academic_year__start_date')
        )['start_date']

    @cached_property
    def valid_end_date(self):
        if not self.validated_agreements.exists():
            return None
        return self.validated_agreements.aggregate(
            end_date=Max('end_academic_year__end_date')
        )['end_date']

    @cached_property
    def validity_end(self):
        is_mobility = self.partnership_type == PartnershipType.MOBILITY.name
        is_project = self.partnership_type == PartnershipType.PROJECT.name
        if is_mobility and hasattr(self, 'validity_end_year'):
            # Queryset was annotated
            if self.validity_end_year is None:
                return None
            return '{0}-{1}'.format(
                self.validity_end_year,
                str(self.validity_end_year + 1)[-2:],
            )
        if is_project:
            return self.end_date.strftime("%d/%m/%Y")
        agreement = (
            self.validated_agreements
                .select_related('end_academic_year')
                .order_by('-end_academic_year__end_date')
                .first()
        )
        if agreement is None:
            return None
        if is_mobility:
            return str(agreement.end_academic_year)
        return agreement.end_date.strftime("%d/%m/%Y")

    @cached_property
    def valid_agreements_dates_ranges(self):
        agreements = self.validated_agreements.prefetch_related(
            'start_academic_year', 'end_academic_year'
        ).values(
            'start_academic_year__year', 'end_academic_year__year'
        ).order_by('start_academic_year__year')
        agreements = [{
            'start': agreement['start_academic_year__year'],
            'end': agreement['end_academic_year__year'],
        } for agreement in agreements]
        return merge_agreement_ranges(list(agreements))

    @cached_property
    def has_missing_valid_years(self):
        """ Test if we have PartnershipYear for all of the partnership duration """
        if self.end_academic_year and self.start_academic_year:
            if len(self.valid_agreements_dates_ranges) == 0:
                return True
            elif len(self.valid_agreements_dates_ranges) > 1:
                return True
            else:
                return (
                    len(self.valid_agreements_dates_ranges) > 1
                    or self.valid_agreements_dates_ranges[0]['start'] > self.start_academic_year.year
                    or self.valid_agreements_dates_ranges[0]['end'] < self.end_academic_year.year
                )
        return False

    @cached_property
    def current_year(self):
        now = timezone.now()
        return (
            self.years
                .filter(academic_year__start_date__lte=now, academic_year__end_date__gte=now)
                .prefetch_related('education_fields', 'education_levels')
                .first()
        )

    @cached_property
    def entities_acronyms(self):
        """
        The following attributes come from add_acronyms() annotations
        """
        entities = []
        if self.ucl_sector_most_recent_acronym:
            entities.append(format_html(
                '<abbr title="{0}">{1}</abbr>',
                self.ucl_sector_most_recent_title,
                self.ucl_sector_most_recent_acronym,
            ))
        if self.ucl_faculty_most_recent_acronym:
            entities.append(format_html(
                '<abbr title="{0}">{1}</abbr>',
                self.ucl_faculty_most_recent_title,
                self.ucl_faculty_most_recent_acronym,
            ))
        if self.ucl_entity_most_recent_acronym:
            entities.append(format_html(
                '<abbr title="{0}">{1}</abbr>',
                self.ucl_entity_most_recent_title,
                self.ucl_entity_most_recent_acronym,
            ))
        return mark_safe(' / '.join(entities))

    def get_supervisor(self):
        if self.supervisor is not None:
            return self.supervisor
        if not hasattr(self.ucl_entity, 'uclmanagement_entity'):
            return None
        return self.ucl_entity.uclmanagement_entity.academic_responsible
