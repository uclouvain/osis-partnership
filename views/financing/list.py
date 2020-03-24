from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView

from base.models.academic_year import AcademicYear
from base.utils.search import SearchMixin
from partnership import perms
from partnership.api.serializers.financing import FinancingSerializer
from partnership.filter import FinancingAdminFilter
from partnership.forms import FinancingFilterForm, FinancingImportForm
from partnership.models import Financing, PartnershipConfiguration
from partnership.utils import user_is_adri
from reference.models.country import Country

__all__ = [
    'FinancingListView',
]


class FinancingListView(UserPassesTestMixin, SearchMixin, FormMixin, FilterView):
    template_name = "partnerships/financings/financing_list.html"
    form_class = FinancingFilterForm
    context_object_name = "countries"
    paginate_by = 25
    login_url = 'access_denied'
    serializer_class = FinancingSerializer
    filterset_class = FinancingAdminFilter
    cache_search = False

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user_is_adri(user)

    def dispatch(self, *args, year=None, **kwargs):
        if year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        else:
            self.academic_year = get_object_or_404(AcademicYear, year=year)

        if self.request.method == "POST":
            self.import_form = FinancingImportForm(self.request.POST, self.request.FILES)
            self.form = FinancingFilterForm(self.request.POST)
        else:
            self.import_form = FinancingImportForm(initial={'import_academic_year': self.academic_year})
            self.form = FinancingFilterForm(initial={'year': self.academic_year})
        return super().dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        if self.form.is_valid():
            return self.form_valid(self.form)
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context['import_form'] = self.import_form
        context['can_import_financing'] = perms.user_can_import_financing(user)
        context['can_export_financing'] = perms.user_can_export_financing(user)
        context['academic_year'] = self.academic_year
        return context

    def get_success_url(self):
        return reverse('partnerships:financings:list', kwargs={'year': self.academic_year.year})

    def get_queryset(self):
        return (
            Country.objects
            .annotate(
                financing_name=Subquery(
                    Financing.objects
                        .filter(countries=OuterRef('pk'), academic_year=self.academic_year)
                        .values('name')[:1]
                ),
                financing_url=Subquery(
                    Financing.objects
                        .filter(countries=OuterRef('pk'), academic_year=self.academic_year)
                        .values('url')[:1]
                ),
            )
            .distinct()
        )

    def form_valid(self, form):
        self.academic_year = form.cleaned_data.get('year', None)
        if self.academic_year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        return redirect(self.get_success_url())

    def get_paginate_by(self, queryset):
        return self.paginate_by
