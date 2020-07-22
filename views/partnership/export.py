from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Case, Exists, OuterRef, Prefetch, Subquery, When
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy as _

from base.models.academic_year import AcademicYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from partnership.models import (
    PartnershipAgreement,
    PartnershipType,
    PartnershipYear,
    AgreementStatus,
    Financing,
)
from .list import PartnershipsListView
from ..export import ExportView

__all__ = [
    'PartnershipExportView',
]


class PartnershipExportView(ExportView, PartnershipsListView):
    academic_year = None

    def get(self,  *args, **kwargs):
        pk = kwargs.pop('academic_year_pk')
        self.academic_year = get_object_or_404(AcademicYear, pk=pk)
        return super().get(*args, **kwargs)

    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('partnership_type'),
            gettext('partnership_subtype'),
            gettext('funding_source'),
            gettext('funding_program'),
            gettext('funding_type'),
            gettext('continent'),
            gettext('country'),
            gettext('partner'),
            gettext('partner_code'),
            gettext('erasmus_code'),
            gettext('pic_code'),
            gettext('partner_entity'),
            gettext('sector'),
            gettext('ucl_university'),
            gettext('ucl_university_labo'),
            gettext('supervisor'),
            gettext('partnership_year_entities'),
            gettext('partnership_year_education_levels'),
            gettext('tags'),
            gettext('created'),
            gettext('modified'),
            gettext('author'),
            gettext('is_sms'),
            gettext('is_smp'),
            gettext('is_sta'),
            gettext('is_stt'),
            gettext('partnership_export_start'),
            gettext('partnership_export_end'),
            gettext('end_valid_agreement'),
            gettext('is_valid'),
            gettext('external_id'),
            gettext('eligible'),
        ]

    def get_xls_data(self):
        queryset = self.filterset.qs
        year_qs = PartnershipYear.objects.select_related(
            'academic_year',
            'subtype',
            'funding_source',
            'funding_program',
            'funding_type',
        ).prefetch_related(
            Prefetch('entities', queryset=Entity.objects.annotate(
                most_recent_acronym=Subquery(EntityVersion.objects.filter(
                    entity=OuterRef('pk')
                ).order_by('-start_date').values('acronym')[:1]),
            )),
            'education_levels',
        ).filter(academic_year=self.academic_year)
        queryset = (
            queryset
            .annotate(
                tags_list=StringAgg('tags__value', ', '),
                is_valid=Case(
                    When(
                        partnership_type=PartnershipType.PROJECT.name,
                        then=True,
                    ),
                    default=Exists(
                        PartnershipAgreement.objects.filter(
                            status=AgreementStatus.VALIDATED.name,
                            partnership=OuterRef('pk'),
                        )
                    )
                ),
                financing_source=Subquery(Financing.objects.filter(
                    countries=OuterRef('partner__contact_address__country'),
                    academic_year=self.academic_year,
                ).values('type__program__source')[:1]),
                financing_program=Subquery(Financing.objects.filter(
                    countries=OuterRef('partner__contact_address__country'),
                    academic_year=self.academic_year,
                ).values('type__program')[:1]),
                financing_type=Subquery(Financing.objects.filter(
                    countries=OuterRef('partner__contact_address__country'),
                    academic_year=self.academic_year,
                ).values('type')[:1]),
            )
            .prefetch_related(
                Prefetch(
                    'years',
                    queryset=year_qs,
                    to_attr='selected_year',
                ),
                Prefetch(
                    'years',
                    queryset=PartnershipYear.objects.select_related('academic_year'),
                ),
                Prefetch(
                    'years',
                    queryset=PartnershipYear.objects.select_related('academic_year').reverse(),
                    to_attr='reverse_years',
                ),
                Prefetch(
                    'agreements',
                    queryset=PartnershipAgreement.objects.filter(
                        status=AgreementStatus.VALIDATED.name,
                    ).select_related('end_academic_year').order_by('-end_date'),
                    to_attr='last_agreement',
                ),
            )
            .select_related(
                'author__user',
                'partner__organization',
                'partner__contact_address__country__continent',
            )
            .filter(
                years__academic_year=self.academic_year,
            )
        )
        for partnership in queryset.distinct():
            year = partnership.selected_year[0]
            last_agreement = partnership.last_agreement[0] if partnership.last_agreement else None

            # Replace funding values if financing is eligible for mobility
            if partnership.is_mobility and year.eligible and partnership.financing_type:
                partnership.funding_source = partnership.financing_source
                partnership.funding_program = partnership.financing_program
                partnership.funding_type = partnership.financing_type

            yield [
                partnership.pk,
                partnership.get_partnership_type_display(),
                str(year.subtype or ''),
                str(year.funding_source or ''),
                str(year.funding_program or ''),
                str(year.funding_type or ''),
                str(partnership.partner.contact_address.country.continent or ''),
                str(partnership.partner.contact_address.country or ''),
                str(partnership.partner),
                str(partnership.partner.organization.code or ''),
                str(partnership.partner.erasmus_code or ''),
                str(partnership.partner.pic_code or ''),
                str(partnership.partner_entity or ''),

                str(partnership.ucl_sector_most_recent_acronym),
                str(partnership.ucl_faculty_most_recent_acronym
                    or partnership.ucl_entity_most_recent_acronym),
                str(partnership.ucl_faculty_most_recent_acronym
                    and partnership.ucl_entity_most_recent_acronym or ''),

                str(partnership.supervisor or ''),
                ', '.join(map(lambda x: x.most_recent_acronym, year.entities.all())),
                ', '.join(map(str, year.education_levels.all())),
                partnership.tags_list,
                partnership.created.strftime('%Y-%m-%d'),
                partnership.modified.strftime('%Y-%m-%d'),
                str(partnership.author.user) if partnership.author else '',

                year.is_sms,
                year.is_smp,
                year.is_sta,
                year.is_stt,

                str(partnership.years.first().academic_year)
                if partnership.is_mobility else partnership.start_date,

                str(partnership.reverse_years[0].academic_year)
                if partnership.is_mobility else partnership.end_date,

                getattr(
                    last_agreement,
                    'end_academic_year' if partnership.is_mobility else 'end_date',
                    '',
                ),

                partnership.is_valid,
                partnership.external_id,
                year.eligible,
            ]

    def get_filename(self):
        return now().strftime('partnerships-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('Partnerships')

    def get_xls_filters(self):
        filters = super().get_xls_filters()
        filters[_('academic_year')] = str(self.academic_year)
        filters.move_to_end(_('academic_year'), last=False)
        return filters
