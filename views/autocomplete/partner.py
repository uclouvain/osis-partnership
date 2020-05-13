from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin

from base.models.entity import Entity
from partnership.models import Partner, PartnerEntity

__all__ = [
    'EntityAutocompleteView',
    'PartnerAutocompleteView',
    'PartnerEntityAutocompleteView',
]


class EntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    # FIXME : doesn't not seem to be used
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Entity.objects.prefetch_related('entityversion_set').all()
        if self.q:
            qs = qs.filter(
                entityversion__acronym__icontains=self.q
            )
        return qs.distinct()


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
        qs = Partner.objects.all()
        pk = self.forwarded.get('partner_pk', None)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        qs = qs.distinct()
        if pk is not None:
            current = Partner.objects.get(pk=pk)
            return [current] + list(filter(lambda x: x.is_actif, qs))
        return list(filter(lambda x: x.is_actif, qs))


class PartnerEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = PartnerEntity.objects.all()
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(partner=partner)
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()
