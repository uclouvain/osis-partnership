import csv

from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from base.models.academic_year import AcademicYear
from osis_common.decorators.download import set_download_cookie
from osis_role.contrib.views import PermissionRequiredMixin
from partnership.models import Financing, PartnershipConfiguration
from reference.models.country import Country

__all__ = [
    'FinancingExportView',
]


class FinancingExportView(PermissionRequiredMixin, View):
    login_url = 'access_denied'
    permission_required = 'partnership.export_financing'

    def get_csv_data(self, academic_year):
        countries = Country.objects.all().order_by('name').prefetch_related(
            Prefetch(
                'financing_set',
                queryset=Financing.objects.select_related(
                    'academic_year',
                    'type__program__source'
                ).filter(academic_year=academic_year)
            )
        )
        for country in countries:
            if country.financing_set.all():
                for financing in country.financing_set.all():
                    row = {
                        'country': country.iso_code,
                        'country_name': country.name,
                        'name': financing.type.name,
                        'url': financing.type.url,
                        'program': financing.type.program,
                        'source': financing.type.program.source,
                    }
                    yield row
            else:
                row = {
                    'country': country.iso_code,
                    'country_name': country.name,
                    'name': '',
                    'url': '',
                    'program': '',
                    'source': '',
                }
                yield row

    @set_download_cookie
    def get(self, *args, year=None, **kwargs):
        if year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        else:
            self.academic_year = get_object_or_404(AcademicYear, year=year)

        filename = "financings_{}".format(self.academic_year)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(filename)

        fieldnames = ['country_name', 'country', 'name', 'url', 'program', 'source']
        wr = csv.DictWriter(response, delimiter=';', quoting=csv.QUOTE_NONE, fieldnames=fieldnames)
        wr.writeheader()
        for row in self.get_csv_data(academic_year=self.academic_year):
            wr.writerow(row)
        return response
