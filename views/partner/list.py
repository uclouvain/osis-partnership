from datetime import datetime

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, Subquery, OuterRef
from django_filters.views import FilterView

from base.models.entity_version import EntityVersion
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
        now = datetime.now()
        return (
            Partner.objects
            .select_related('contact_address__country')
            .add_dates_annotation()
            .annotate(
                partnerships_count=Count('partnerships'),
                website=Subquery(EntityVersion.objects.current(now).filter(
                    entity__organization=OuterRef('organization_id'),
                    parent__isnull=True,
                ).order_by('-start_date').values('entity__website')[:1])
            ).distinct()
        )

    def get_paginate_by(self, queryset):
        return 20
