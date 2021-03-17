from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Subquery, F, Prefetch
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from base.models.academic_year import AcademicYear
from base.utils.search import SearchMixin
from partnership.api.serializers import PartnershipPartnerRelationAdminSerializer
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.filter import PartnershipAdminFilter
from partnership.models import (
    Partnership, PartnershipType, PartnershipPartnerRelation,
)

__all__ = [
    'PartnershipsListView',
]


class PartnershipsListView(PermissionRequiredMixin, SearchMixin, FilterView):
    template_name = 'partnerships/partnership/partnership_list.html'
    context_object_name = 'partnerships'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'
    serializer_class = PartnershipPartnerRelationAdminSerializer
    filterset_class = PartnershipAdminFilter
    cache_search = False

    def get_queryset(self):
        return (
            PartnershipPartnerRelation.objects
            .annotate_partner_address(
                'country__continent_id',
                'country__name',
                'country_id',
                'city',
            )
            .add_acronyms()  # for ordering
            .select_related(
                'entity__organization__partner',
            )
            .prefetch_related(
                Prefetch(
                    'partnership',
                    queryset=Partnership.objects.add_acronyms().for_validity_end().select_related(
                        'supervisor',
                        'subtype',  # keep for xls export
                        'ucl_entity__uclmanagement_entity__academic_responsible',
                    ),
                ),
            )
            # TODO remove when Entity city field is dropped (conflict)
            .defer("partnership__ucl_entity__city")
        ).distinct().order_by('pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "application/json" in self.request.headers.get("Accept", ""):
            return context
        user = self.request.user
        context['can_change_configuration'] = is_linked_to_adri_entity(user)
        context['can_add_partnership'] = any([
            t for t in PartnershipType
            if user.has_perm('partnership.add_partnership', t)]
        )
        context['url'] = reverse('partnerships:list')
        context['search_button_label'] = _('search_partnership')
        context['export_years'] = AcademicYear.objects.annotate(
            current_year=Subquery(AcademicYear.objects.currents().values('year')[:1]),
        ).filter(
            year__gte=F('current_year'),
        ).order_by('year')[:3]
        return context

    def get_paginate_by(self, queryset):
        if "application/json" not in self.request.headers.get("Accept", ""):
            return None
        return 20
