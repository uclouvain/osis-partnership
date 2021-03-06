from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q, F

from partnership.models import EntityProxy
from partnership.utils import format_partner_entity

__all__ = [
    'PartnerEntityAutocompleteView',
]


class PartnerEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    """ Autocomplete used on partnership form"""
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partners'

    def get_queryset(self):
        qs = EntityProxy.objects.partner_entities().order_by(
            'organization__name',
            F('partnerentity__name').asc(nulls_first=True),
        )
        if self.q:
            qs = qs.filter(
                Q(organization__name__icontains=self.q)
                | Q(partnerentity__name__icontains=self.q)
                | Q(organization__code__icontains=self.q)
            )
        return qs.distinct()

    def get_result_label(self, result):
        return format_partner_entity(result)
