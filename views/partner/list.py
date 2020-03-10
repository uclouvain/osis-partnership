from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count
from django_filters.views import FilterView

from base.utils.search import SearchMixin
from partnership import perms
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
            Partner.objects.all()
            .select_related('partner_type', 'contact_address__country')
            .annotate(partnerships_count=Count('partnerships')).distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_add_partner'] = perms.user_can_add_partner(self.request.user)
        return context

    def get_paginate_by(self, queryset):
        return 20
