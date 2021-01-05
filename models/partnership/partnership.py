import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, Min, Prefetch, OuterRef, Subquery, Q
from django.db.models.functions import Now
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from base.models.entity_version import EntityVersion
from base.utils.cte import CTESubquery
from partnership.models import AgreementStatus, PartnershipType, Financing
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
        ref = models.OuterRef('ucl_entity_id')

        return self.annotate(
            acronym_path=CTESubquery(
                EntityVersion.objects.with_acronym_path(
                    entity_id=ref
                ).values('acronym_path')[:1]
            ),
            title_path=CTESubquery(
                EntityVersion.objects.with_acronym_path(
                    entity_id=ref
                ).values('title_path')[:1]
            ),
        )

    def for_validity_end(self):
        from .agreement import PartnershipAgreement
        from .partnership_year import PartnershipYear
        return self.prefetch_related(
            Prefetch(
                'agreements',
                PartnershipAgreement.objects.filter(
                    status=AgreementStatus.VALIDATED.name,
                ).select_related('end_academic_year').order_by(
                    '-end_academic_year__end_date'
                ),
                to_attr='last_valid_agreements',
            ),
            Prefetch(
                'years',
                PartnershipYear.objects.order_by(
                    '-academic_year__end_date',
                ).select_related('academic_year'),
                to_attr='last_years',
            ),
        )

    def annotate_partner_address(self, *fields):
        """
        Add annotations on partner contact address

        :param fields: list of fields relative to EntityVersionAddress
            If a field contains a traversal, e.g. country__name, it will be
            available as country_name
        """
        contact_address_qs = EntityVersion.objects.filter(
            entity__organization=OuterRef('partner__organization'),
            parent__isnull=True,
        ).order_by('-start_date')
        qs = self
        for field in fields:
            lookup = Subquery(contact_address_qs.values(
                'entityversionaddress__{}'.format(field)
            )[:1])
            qs = qs.annotate(**{field.replace('__', '_'): lookup})
        return qs

    def annotate_financing(self, academic_year):
        """
        Add annotations to get funding for an academic year based on country
        """
        return self.annotate(
            financing_source=Subquery(Financing.objects.filter(
                countries=OuterRef('country_id'),
                academic_year=academic_year,
            ).values('type__program__source__name')[:1]),
            financing_program=Subquery(Financing.objects.filter(
                countries=OuterRef('country_id'),
                academic_year=academic_year,
            ).values('type__program__name')[:1]),
            financing_type=Subquery(Financing.objects.filter(
                countries=OuterRef('country_id'),
                academic_year=academic_year,
            ).values('type__name')[:1]),
        )

    def filter_for_api(self, academic_year):
        from partnership.models import PartnershipYear, PartnershipAgreement
        return self.annotate(
            current_academic_year=models.Value(
                academic_year.id, output_field=models.AutoField()
            ),
        ).annotate(
            has_years_in=models.Exists(
                PartnershipYear.objects.filter(
                    partnership=OuterRef('pk'),
                    academic_year=academic_year,
                )
            ),
            has_valid_agreement_in_current_year=models.Exists(
                PartnershipAgreement.objects.filter(
                    partnership=OuterRef('pk'),
                    status=AgreementStatus.VALIDATED.name,
                    start_academic_year__year__lte=academic_year.year,
                    end_academic_year__year__gte=academic_year.year,
                )
            ),
        ).filter(
            # If mobility, should have agreement for current year
            # and have a partnership year for current year
            Q(
                partnership_type=PartnershipType.MOBILITY.name,
                has_valid_agreement_in_current_year=True,
                has_years_in=True,
            )
            # Else all other types do not need agreement
            | (
                    ~Q(partnership_type=PartnershipType.MOBILITY.name)
                    & Q(end_date__gte=Now())
            ),
            # And must be public
            is_public=True,
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
        db_index=True,
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
        'base.Entity',
        verbose_name=_('partner_entity'),
        on_delete=models.PROTECT,
        related_name='partnerships_from_partnerentity',
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

    missions = models.ManyToManyField(
        'partnership.PartnershipMission',
        verbose_name=_('partnership_missions'),
    )
    subtype = models.ForeignKey(
        'partnership.PartnershipSubtype',
        verbose_name=_('partnership_subtype'),
        on_delete=models.PROTECT,
        related_name='years',
        null=True,
    )
    description = models.TextField(
        _('partnership_year_description'),
        help_text=_('visible_on_api'),
        default='',
        blank=True,
    )

    # For PROJECT type
    ucl_status = models.CharField(
        verbose_name=_('partnership_year_ucl_status'),
        max_length=20,
        default='',
        choices=[
            ('coordinator', _('Coordinator')),
            ('partner', _('Partner')),
        ],
    )
    id_number = models.CharField(
        verbose_name=_('partnership_year_id_number'),
        max_length=200,
        default='',
    )
    project_title = models.CharField(
        verbose_name=_('partnership_year_project_title'),
        max_length=200,
        default='',
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
        return self.is_project or self.validated_agreements.exists()

    @property
    def validated_agreements(self):
        return self.agreements.filter(status=AgreementStatus.VALIDATED.name).order_by('start_academic_year__year')

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
        if (self.is_general or self.is_project) and self.end_date:
            return self.end_date.strftime("%d/%m/%Y")
        # Queryset must be annotated with for_validity_end()
        if self.is_mobility and self.last_valid_agreements:
            # End academic year of the agreement
            return str(self.last_valid_agreements[0].end_academic_year)
        if (self.is_course or self.is_doctorate) and self.last_years:
            # Academic year of the last partnership year
            return str(self.last_years[0].academic_year)

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

    is_general = property(lambda self: self.partnership_type == PartnershipType.GENERAL.name)
    is_mobility = property(lambda self: self.partnership_type == PartnershipType.MOBILITY.name)
    is_course = property(lambda self: self.partnership_type == PartnershipType.COURSE.name)
    is_doctorate = property(lambda self: self.partnership_type == PartnershipType.DOCTORATE.name)
    is_project = property(lambda self: self.partnership_type == PartnershipType.PROJECT.name)

    @cached_property
    def entities_acronyms(self):
        """
        The following attributes come from add_acronyms() annotations
        """
        if not self.acronym_path:
            return ''
        entities = []
        for i in range(1, len(self.acronym_path)):
            entities.append(format_html(
                '<abbr title="{0}">{1}</abbr>',
                self.title_path[i],
                self.acronym_path[i],
            ))
        return mark_safe(' / '.join(entities))

    def get_supervisor(self):
        if self.supervisor is not None:
            return self.supervisor
        if not hasattr(self.ucl_entity, 'uclmanagement_entity'):
            return None
        return self.ucl_entity.uclmanagement_entity.academic_responsible
