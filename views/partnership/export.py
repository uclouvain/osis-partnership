from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Case, Exists, OuterRef, Prefetch, When
from django.db.models.expressions import Subquery
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy as _

from base.models.academic_year import AcademicYear
from partnership.models import (
    EntityProxy,
    Partnership,
    PartnershipAgreement,
    PartnershipType,
    PartnershipYear,
    AgreementStatus,
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
            gettext('is_sms'),
            gettext('is_smp'),
            gettext('is_sta'),
            gettext('is_stt'),
            gettext('partnership_export_start'),
            gettext('partnership_export_end'),
            gettext('end_valid_agreement'),
            gettext('is_valid'),
            gettext('external_id'),
            gettext('partnership_project_acronym'),
            gettext('eligible'),
        ]

    def get_xls_data(self):
        queryset = self.filterset.qs
        year_qs = PartnershipYear.objects.select_related(
            'academic_year',
            'funding_source',
            'funding_program',
            'funding_type',
        ).prefetch_related(
            Prefetch('entities', queryset=EntityProxy.objects.with_acronym()),
            'education_levels',
        ).filter(academic_year=self.academic_year)
        queryset = (
            queryset
            .annotate_financing(self.academic_year)
            .annotate_partner_address('country__continent__name')
            .annotate(
                tags_list=Subquery(
                    Partnership.objects.filter(pk=OuterRef('partnership__pk')).annotate(
                        tags_list=StringAgg('tags__value', ', '),
                    ).values('tags_list')[:1]
                ),
                is_valid_for_year=Case(
                    When(
                        partnership__partnership_type=PartnershipType.PROJECT.name,
                        then=True,
                    ),
                    default=Exists(
                        PartnershipAgreement.objects.filter(
                            partnership=OuterRef('partnership_id'),
                            status=AgreementStatus.VALIDATED.name,
                            start_academic_year__year__lte=self.academic_year.year,
                            end_academic_year__year__gte=self.academic_year.year,
                        )
                    )
                ),
            )
            .prefetch_related(
                Prefetch(
                    'partnership__years',
                    queryset=year_qs,
                    to_attr='selected_year',
                ),
                Prefetch(
                    'partnership__years',
                    queryset=PartnershipYear.objects.select_related('academic_year'),
                ),
                Prefetch(
                    'partnership__years',
                    queryset=PartnershipYear.objects.select_related('academic_year').reverse(),
                    to_attr='reverse_years',
                ),
                'entity__entityversion_set',
            )
            .select_related(
                'entity__partnerentity',
            )
        )
        for rel in queryset.distinct():
            partnership = rel.partnership
            year = partnership.selected_year[0] if partnership.selected_year else ''
            last_agreement = partnership.last_valid_agreements[0] if partnership.last_valid_agreements else None

            # Replace funding values if financing is eligible for mobility and not overridden in year
            if partnership.is_mobility and year and year.eligible and rel.financing_source and not year.funding_source:
                funding_source = rel.financing_source
                funding_program = rel.financing_program
                funding_type = rel.financing_type
            else:
                funding_source = year and year.funding_source
                funding_program = year and year.funding_program
                funding_type = year and year.funding_type

            parts = partnership.acronym_path[1:] if partnership.acronym_path else []

            partner = rel.entity.organization.partner
            yield [
                partnership.pk,
                partnership.get_partnership_type_display(),
                str(partnership.subtype or ''),
                str(funding_source or ''),
                str(funding_program or ''),
                str(funding_type or ''),
                str(rel.country_continent_name),
                str(rel.country_name),
                str(rel.entity.organization.name),
                str(rel.entity.organization.code or ''),
                str(partner.erasmus_code or ''),
                str(partner.pic_code or ''),

                hasattr(rel.entity, 'partnerentity')
                and rel.entity.partnerentity.name or '',

                str(parts[0] if len(parts) > 0 else ''),
                str(parts[1] if len(parts) > 1 else ''),
                str(parts[2] if len(parts) > 2 else ''),

                str(partnership.supervisor or ''),
                year and ', '.join(map(lambda x: x.acronym or '', year.entities.all())),
                year and ', '.join(map(str, year.education_levels.all())),
                rel.tags_list,
                partnership.created.strftime('%Y-%m-%d'),
                partnership.modified.strftime('%Y-%m-%d'),

                year and year.is_sms,
                year and year.is_smp,
                year and year.is_sta,
                year and year.is_stt,

                str(partnership.years.first().academic_year)
                if partnership.is_mobility else partnership.start_date,

                str(partnership.reverse_years[0].academic_year)
                if partnership.is_mobility else partnership.end_date,

                getattr(
                    last_agreement,
                    'end_academic_year' if partnership.is_mobility else 'end_date',
                    '',
                ),

                rel.is_valid_for_year,  # from annotation
                partnership.external_id,
                partnership.project_acronym,
                year and year.eligible,
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
