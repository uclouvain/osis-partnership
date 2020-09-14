from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy as _

from partnership.utils import academic_years
from .list import PartnershipAgreementListView
from ..export import ExportView

__all__ = ['PartnershipAgreementExportView']


class PartnershipAgreementExportView(ExportView, PartnershipAgreementListView):
    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('partnership_type'),
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
        for agreement in self.filterset.qs:
            years = academic_years(agreement.start_academic_year, agreement.end_academic_year)
            parts = agreement.acronym_path
            yield [
                agreement.pk,
                agreement.partnership.get_partnership_type_display(),
                str(agreement.partnership.partner),
                str(agreement.country_name),
                str(agreement.city),
                str(agreement.partnership.supervisor),
                parts[1] if len(parts) > 1 else "",
                parts[2] if len(parts) > 2 else "",
                years,
                agreement.start_academic_year.year,
                agreement.end_academic_year.year + 1,
                agreement.get_status_display(),
            ]

    def get_description(self):
        return _('Agreements')

    def get_filename(self):
        return now().strftime('agreements-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('Agreements')
