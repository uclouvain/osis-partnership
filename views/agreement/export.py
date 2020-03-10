from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy as _

from base.models.entity_version import EntityVersion
from partnership.utils import academic_years
from ..export import ExportView
from ..partnership.mixins import PartnershipListFilterMixin

__all__ = ['PartnershipAgreementExportView']


class PartnershipAgreementExportView(PermissionRequiredMixin,
                                     PartnershipListFilterMixin,
                                     ExportView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    @cached_property
    def is_agreements(self):
        return True

    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('partner'),
            gettext('country'),
            gettext('city'),
            gettext('partnership_supervisor'),
            gettext('faculty'),
            gettext('entity'),
            gettext('academic_years'),
            gettext('start_academic_year'),
            gettext('end_academic_year'),
            gettext('status'),
        ]

    def get_xls_data(self):
        queryset = self.get_queryset().prefetch_related(
            Prefetch(
                'partnership__ucl_university__entityversion_set',
                queryset=EntityVersion.objects.order_by('start_date'),
                to_attr='faculties',
            ),
        )
        for agreement in queryset:
            faculty = agreement.partnership.ucl_university.faculties[0]
            entity = agreement.partnership.ucl_university_labo
            years = academic_years(agreement.start_academic_year, agreement.end_academic_year)
            yield [
                agreement.pk,
                str(agreement.partnership.partner),
                str(agreement.partnership.partner.contact_address.country),
                str(agreement.partnership.partner.contact_address.city),
                str(agreement.partnership.supervisor),
                faculty.acronym,
                entity.most_recent_acronym if entity is not None else '',
                years,
                agreement.start_academic_year.year,
                agreement.end_academic_year.year + 1,
                agreement.get_status_display(),
            ]

    def get_description(self):
        return _('agreements')

    def get_filename(self):
        return now().strftime('agreements-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('agreements')