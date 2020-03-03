import codecs
import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin, ProcessFormView

from partnership.forms import FinancingImportForm
from partnership.models import Financing, PartnershipConfiguration
from partnership.utils import user_is_adri
from reference.models.country import Country

__all__ = [
    'FinancingImportView',
]


class FinancingImportView(LoginRequiredMixin, UserPassesTestMixin, TemplateResponseMixin, FormMixin, ProcessFormView):
    form_class = FinancingImportForm
    template_name = "partnerships/financings/financing_import.html"
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_success_url(self, academic_year=None):
        if academic_year is None:
            configuration = PartnershipConfiguration.get_configuration()
            academic_year = configuration.get_current_academic_year_for_creation_modification()
        return reverse('partnerships:financings:list', kwargs={'year': academic_year.year})

    def get_reader(self, csv_file):
        sample = csv_file.read(1024).decode('utf8')
        dialect = csv.Sniffer().sniff(sample)
        csv_file.seek(0)
        reader = csv.DictReader(
            codecs.iterdecode(csv_file, 'utf8'),
            fieldnames=['country_name', 'country', 'name', 'url'],
            dialect=dialect,
        )
        return reader

    def handle_csv(self, reader):
        url_validator = URLValidator()
        financings_countries = {}
        financings_url = {}
        next(reader, None)
        for row in reader:
            if not row['name']:
                continue
            try:
                country = Country.objects.get(iso_code=row['country'])
            except Country.DoesNotExist:
                messages.warning(
                    self.request, _('financing_country_not_imported_{country}').format(country=row['country']))
                continue
            if row['name'] not in financings_url:
                url = row['url']
                try:
                    if url:
                        url_validator(url)
                    financings_url[row['name']] = url
                except ValidationError:
                    financings_url[row['name']] = ''
                    messages.warning(
                        self.request, _('financing_url_invalid_{country}_{url}').format(country=country, url=url))
            financings_countries.setdefault(row['name'], []).append(country)
        return financings_countries, financings_url

    @transaction.atomic
    def update_financings(self, academic_year, financings_countries, financings_url):
        Financing.objects.filter(academic_year=academic_year).delete()
        financings = []
        for name in financings_countries.keys():
            financings.append(
                Financing(
                    academic_year=academic_year,
                    name=name,
                    url=financings_url.get(name, None)
                )
            )
        financings = Financing.objects.bulk_create(financings)
        for financing in financings:
            financing.countries.set(financings_countries.get(financing.name, []))

    def form_valid(self, form):
        academic_year = form.cleaned_data.get('import_academic_year')

        reader = self.get_reader(self.request.FILES['csv_file'])
        try:
            financings_countries, financings_url = self.handle_csv(reader)
        except ValueError:
            messages.error(self.request, _('financings_imported_error'))
            return redirect(self.get_success_url(academic_year))

        self.update_financings(academic_year, financings_countries, financings_url)

        messages.success(self.request, _('financings_imported'))
        return redirect(self.get_success_url(academic_year))
