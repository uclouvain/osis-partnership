import codecs
import csv
from collections import defaultdict

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.shortcuts import redirect, resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin, ProcessFormView

from osis_role.contrib.views import PermissionRequiredMixin
from partnership.forms import FinancingImportForm
from partnership.models import (
    Financing, FundingProgram, FundingSource,
    FundingType,
)
from reference.models.country import Country

__all__ = [
    'FinancingImportView',
]


class FinancingImportView(PermissionRequiredMixin, TemplateResponseMixin, FormMixin, ProcessFormView):
    form_class = FinancingImportForm
    template_name = "partnerships/financings/financing_import.html"
    login_url = 'access_denied'
    permission_required = 'partnership.import_financing'

    def get_success_url(self, academic_year=None):
        return resolve_url('partnerships:financings:list', year=academic_year.year)

    def get_reader(self, csv_file):
        sample = csv_file.read(1024).decode('utf8')
        dialect = csv.Sniffer().sniff(sample)
        csv_file.seek(0)
        reader = csv.DictReader(
            codecs.iterdecode(csv_file, 'utf8'),
            fieldnames=['country_name', 'country', 'name', 'url', 'program', 'source'],
            dialect=dialect,
        )
        return reader

    def get_with_warning(self, row, field, references):
        """
        Fetch a named column from the row, displaying a warning if missing
        from the references
        """
        obj = references.get(row[field])
        if not obj:
            messages.warning(
                self.request,
                _('financing_{field}_not_imported_{value}').format(
                    field=field, value=row[field],
                )
            )
        return obj

    def handle_csv(self, reader):
        url_validator = URLValidator()
        results = defaultdict(lambda: {
            'countries': [],
            'url': '',
            # program: None
        })

        # Skip first line (headers)
        next(reader, None)

        # Performance trick: load all known countries, sources and programs
        countries = {c.iso_code: c for c in Country.objects.all()}
        programs = {p.name: p for p in FundingProgram.objects.all()}
        sources = {s.name: s for s in FundingSource.objects.all()}

        for row in reader:
            if not row['name']:
                continue

            # Fetch each field
            program = self.get_with_warning(row, 'program', programs)
            source = self.get_with_warning(row, 'source', sources)
            country = self.get_with_warning(row, 'country', countries)

            if not program or not source or not country:  # pragma: no cover
                # Actually covered, see https://github.com/nedbat/coveragepy/issues/198
                continue

            result = results[row['name']]

            result['program'] = program
            result['countries'].append(country)

            # Financing url
            if row['url']:
                try:
                    url_validator(row['url'])
                    result['url'] = row['url']
                except ValidationError:
                    messages.warning(
                        self.request,
                        _('financing_url_invalid_{country}_{url}').format(
                            country=country, url=row['url']
                        )
                    )

        return results

    @transaction.atomic
    def update_financings(self, academic_year, data):
        # Deleting existing data for the year
        Financing.objects.filter(academic_year=academic_year).delete()

        financing_list = []
        for name, obj in data.items():
            # Create/update the funding type if not existing
            funding, _ = FundingType.objects.update_or_create(defaults=dict(
                url=obj['url'],
                program=obj['program'],
            ), name=name)

            financing_list.append(Financing(
                academic_year=academic_year,
                type=funding,
            ))

        objects = Financing.objects.bulk_create(financing_list)
        for financing in objects:
            financing.countries.set(data[financing.type.name]['countries'])

    def form_valid(self, form):
        academic_year = form.cleaned_data.get('import_academic_year')

        reader = self.get_reader(self.request.FILES['csv_file'])
        try:
            results = self.handle_csv(reader)
        except ValueError:  # pragma: no cover
            messages.error(self.request, _('financings_imported_error'))
            return redirect(self.get_success_url(academic_year))

        self.update_financings(academic_year, results)

        messages.success(self.request, _('financings_imported'))
        return redirect(self.get_success_url(academic_year))
