from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView

from base.models.academic_year import AcademicYear
from base.utils.search import SearchMixin
from osis_role.contrib.views import PermissionRequiredMixin
from partnership.api.serializers.financing import FinancingSerializer
from partnership.filter import FinancingAdminFilter
from partnership.forms import FinancingFilterForm, FinancingImportForm
from partnership.models import (
    Financing,
    PartnershipConfiguration,
    FundingSource,
)
from reference.models.country import Country

__all__ = [
    'FinancingListView',
]


class FinancingListView(PermissionRequiredMixin, SearchMixin, FormMixin, FilterView):
    template_name = "partnerships/financings/financing_list.html"
    form_class = FinancingFilterForm
    context_object_name = "countries"
    paginate_by = 25
    login_url = 'access_denied'
    serializer_class = FinancingSerializer
    filterset_class = FinancingAdminFilter
    cache_search = False
    permission_required = 'partnership.export_financing'

    def dispatch(self, *args, year=None, **kwargs):
        if year is None:
            config = PartnershipConfiguration.get_configuration()
            self.academic_year = config.partnership_creation_update_min_year
        else:
            self.academic_year = get_object_or_404(AcademicYear, year=year)

        self.import_form = FinancingImportForm(
            self.request.POST or None,
            self.request.FILES or None,
            initial={'import_academic_year': self.academic_year},
        )
        self.form = FinancingFilterForm(
            self.request.POST or None,
            initial={'year': self.academic_year},
        )
        return super().dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        if self.form.is_valid():
            return self.form_valid(self.form)
        self.object_list = []
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = self.import_form
        context['academic_year'] = self.academic_year
        context['fundings'] = FundingSource.objects.prefetch_related(
            'fundingprogram_set',
            'fundingprogram_set__fundingtype_set',
        )
        return context

    def get_success_url(self, year=None):
        return resolve_url('partnerships:financings:list', year=year)

    def get_queryset(self):
        qs = Financing.objects.filter(
            countries=OuterRef('pk'),
            academic_year=self.academic_year,
        )
        return Country.objects.annotate(
            financing_name=Subquery(qs.values('type__name')[:1]),
            financing_url=Subquery(qs.values('type__url')[:1]),
        ).distinct()

    def form_valid(self, form):
        academic_year = form.cleaned_data.get('year', None)
        if academic_year is None:
            configuration = PartnershipConfiguration.get_configuration()
            academic_year = configuration.get_current_academic_year_for_creation_modification()
        return redirect(self.get_success_url(academic_year.year))

    def get_paginate_by(self, queryset):
        if "application/json" not in self.request.headers.get("Accept", ""):
            return None
        return self.paginate_by
