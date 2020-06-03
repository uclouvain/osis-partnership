import csv

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from base.models.academic_year import AcademicYear
from osis_common.decorators.download import set_download_cookie
from partnership.models import Financing, PartnershipConfiguration
from partnership.utils import user_is_adri
from reference.models.country import Country

__all__ = [
    'FinancingExportView',
]


class FinancingExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_csv_data(self, academic_year):
        countries = Country.objects.all().order_by('name').prefetch_related(
            Prefetch(
                'financing_set',
                queryset=Financing.objects.prefetch_related(
                    'academic_year'
                ).filter(academic_year=academic_year)
            )
        )
        for country in countries:
            if country.financing_set.all():
                for financing in country.financing_set.all():
                    row = {
                        'country': country.iso_code,
                        'name': financing.name,
                        'url': financing.url,
                        'country_name': country.name,
                    }
                    yield row
            else:
                row = {
                    'country': country.iso_code,
                    'name': '',
                    'url': '',
                    'country_name': country.name,
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

        fieldnames = ['country_name', 'country', 'name', 'url']
        wr = csv.DictWriter(response, delimiter=';', quoting=csv.QUOTE_NONE, fieldnames=fieldnames)
        wr.writeheader()
        for row in self.get_csv_data(academic_year=self.academic_year):
            wr.writerow(row)
        return response
