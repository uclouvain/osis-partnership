from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count
from django_filters.views import FilterView

from base.utils.search import SearchMixin
from partnership.models import Partner
from ...api.serializers import PartnerAdminSerializer
from ...filter import PartnerAdminFilter

__all__ = [
    'PartnersListView',
]


class PartnersListView(PermissionRequiredMixin, SearchMixin, FilterView):
    context_object_name = 'partners'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'
    template_name = 'partnerships/partners/partners_list.html'
    filterset_class = PartnerAdminFilter
    serializer_class = PartnerAdminSerializer
    cache_search = False

    def get_queryset(self):
        return (
            Partner.objects
            .annotate_dates()
            .annotate_website()
            .annotate_address(
                'country__continent_id',
                'country__name',
                'country_id',
                'city',
            )
            .annotate(
                partnerships_count=Count('partnerships'),
            ).distinct()
        )

    def get_paginate_by(self, queryset):
        if "application/json" not in self.request.headers.get("Accept", ""):
            return None
        return 20
