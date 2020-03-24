from collections import OrderedDict

from django.db.models import QuerySet
from django.views import View
from django.views.generic.edit import FormMixin

from base.models.education_group_year import EducationGroupYear
from osis_common.document import xls_build


class ExportView(FormMixin, View):
    login_url = 'access_denied'

    def get_xls_headers(self):
        raise NotImplementedError

    def get_xls_data(self):
        raise NotImplementedError

    def get_description(self):
        raise NotImplementedError

    def get_filename(self):
        raise NotImplementedError

    def get_title(self):
        raise NotImplementedError

    def get_xls_filters(self):
        form = self.filterset.form
        if form.is_valid():
            filters = {}
            for key, value in form.cleaned_data.items():
                label = form.fields[key].label
                if not value and not isinstance(value, bool):
                    continue
                if isinstance(value, QuerySet):
                    value = ', '.join(map(str, list(value)))
                elif isinstance(value, EducationGroupYear):
                    value = '{0} - {1}'.format(value.acronym, value.title)
                filters[label] = str(value)
            filters = OrderedDict(sorted(filters.items(), key=lambda x: x[0]))
            return filters
        return OrderedDict()

    def generate_xls(self):
        working_sheets_data = self.get_xls_data()
        parameters = {
            xls_build.DESCRIPTION: self.get_title(),
            xls_build.USER: str(self.request.user),
            xls_build.FILENAME: self.get_filename(),
            xls_build.HEADER_TITLES: self.get_xls_headers(),
            xls_build.WS_TITLE: self.get_title(),
        }
        filters = self.get_xls_filters()
        response = xls_build.generate_xls(
            xls_build.prepare_xls_parameters_list(working_sheets_data, parameters),
            filters,
        )
        return response

    def get(self, request, *args, **kwargs):
        self.filterset = self.get_filterset(self.get_filterset_class())
        return self.generate_xls()
