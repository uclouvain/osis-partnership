from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin

from partnership.models import Partner, PartnerEntity

__all__ = [
    'PartnerAutocompleteView',
    'PartnerEntityAutocompleteView',
]


class PartnerAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_results(self, context):
        """Return data for the 'results' key of the response."""
        return [
            {
                'id': self.get_result_value(result),
                'text': self.get_result_label(result),
                'pic_code': result.pic_code,
                'erasmus_code': result.erasmus_code,
            } for result in context['object_list']
        ]

    def get_queryset(self):
        qs = Partner.objects.annotate_dates(filter_value=True).distinct()
        pk = self.forwarded.get('partner_pk', None)
        if self.q:
            qs = qs.filter(organization__name__icontains=self.q)
        if pk is not None:
            current = Partner.objects.get(pk=pk)
            return [current] + list(qs)
        return qs


class PartnerEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        partner = self.forwarded.get('partner', None)
        if not partner:
            return PartnerEntity.objects.none()
        qs = PartnerEntity.objects.filter(
            entity__organization__partner=partner,
        )
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()
