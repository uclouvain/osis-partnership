from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Exists, OuterRef, Prefetch, Subquery
from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy as _

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from partnership.models import (
    PartnershipAgreement, PartnershipYear, PartnershipConfiguration,
    AgreementStatus,
)
from .list import PartnershipsListView

from ..export import ExportView

__all__ = [
    'PartnershipExportView',
]


class PartnershipExportView(ExportView, PartnershipsListView):
    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('partnership_type'),
            gettext('partner'),
            gettext('partner_code'),
            gettext('erasmus_code'),
            gettext('pic_code'),
            gettext('partner_entity'),
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
            gettext('start_academic_year'),
            gettext('end_academic_year'),
            gettext('is_valid'),
            gettext('external_id'),
            gettext('eligible'),
        ]

    def get_xls_data(self):
        queryset = self.filterset.qs
        queryset = (
            queryset
            .annotate(
                tags_list=StringAgg('tags__value', ', '),
                is_valid=Exists(
                    PartnershipAgreement.objects
                        .filter(status=AgreementStatus.VALIDATED.name,
                                partnership=OuterRef('pk'))
                ),
            )
            .prefetch_related(
                Prefetch(
                    'years',
                    queryset=PartnershipYear.objects
                        .select_related('academic_year')
                        .prefetch_related(
                            Prefetch(
                                'entities',
                                queryset=Entity.objects.annotate(
                                    most_recent_acronym=Subquery(
                                        EntityVersion.objects
                                            .filter(entity=OuterRef('pk'))
                                            .order_by('-start_date')
                                            .values('acronym')[:1]
                                    ),
                                )
                            ),
                            'education_levels',
                        )
                ),
            )
            .select_related('author__user')
        )
        for partnership in queryset.distinct():

            first_year = None
            current_year = None
            end_year = None
            years = partnership.years.all()
            if years:
                first_year = years[0]
            for year in years:
                end_year = year
                if year.academic_year == self.academic_year:
                    current_year = year

            yield [
                partnership.pk,
                partnership.get_partnership_type_display(),
                str(partnership.partner),
                str(partnership.partner.partner_code) if partnership.partner.partner_code is not None else '',
                str(partnership.partner.erasmus_code) if partnership.partner.erasmus_code is not None else '',
                str(partnership.partner.pic_code) if partnership.partner.pic_code is not None else '',
                str(partnership.partner_entity) if partnership.partner_entity else None,
                str(partnership.ucl_faculty_most_recent_acronym)
                    if partnership.ucl_faculty_most_recent_acronym is not None
                    else partnership.ucl_entity_most_recent_acronym,
                str(partnership.ucl_entity_most_recent_acronym)
                    if partnership.ucl_faculty_most_recent_acronym is not None else '',
                str(partnership.supervisor) if partnership.supervisor is not None else '',
                ', '.join(map(lambda x: x.most_recent_acronym, current_year.entities.all()))
                    if current_year is not None else '',
                ', '.join(map(str, current_year.education_levels.all())) if current_year is not None else '',
                partnership.tags_list,
                partnership.created.strftime('%Y-%m-%d'),
                partnership.modified.strftime('%Y-%m-%d'),
                str(partnership.author.user) if partnership.author else '',
                current_year.is_sms if current_year is not None else '',
                current_year.is_smp if current_year is not None else '',
                current_year.is_sta if current_year is not None else '',
                current_year.is_stt if current_year is not None else '',
                first_year.academic_year if first_year is not None else '',
                end_year.academic_year if end_year is not None else '',
                partnership.is_valid,
                partnership.external_id,
                current_year.eligible if current_year is not None else '',
            ]

    def get_description(self):
        return _('Partnerships')

    def get_filename(self):
        return now().strftime('partnerships-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('Partnerships')

    def get_xls_filters(self):
        filters = super().get_xls_filters()
        filters[_('academic_year')] = str(self.academic_year)
        filters.move_to_end(_('academic_year'), last=False)
        return filters

    def get(self, *args, **kwargs):
        configuration = PartnershipConfiguration.get_configuration()
        self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        return super().get(*args, **kwargs)
