from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q, F

from partnership.models import EntityProxy, PartnershipPartnerRelation
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


class PartnerEntityReferenceAutocompleteView(PartnerEntityAutocompleteView):
    """ Autocomplete used on partnership form"""
    def get_queryset(self):
        qs = super().get_queryset()
        param = self.forwarded.get("partner_entities", None)
        if param:
            qs = qs.filter(pk__in=param)
        return qs

    def get_result_label(self, result):
        return format_partner_entity(result)


class PartnershipPartnerRelationCompleteView(PartnerEntityAutocompleteView):
    """ Autocomplete used on partnership relation form"""
    def get_queryset(self):
        qs = super().get_queryset()
        param = self.forwarded.get("partnership", None)
        entities = PartnershipPartnerRelation.objects.filter(partnership=param).values_list('entity')
        if entities:
            qs = qs.filter(pk__in=entities)
        return qs

    def get_result_label(self, result):
        return format_partner_entity(result)


class PartnerEntityReferenceAutocompleteView(PartnerEntityAutocompleteView):
    """ Autocomplete used on partnership form"""

    def get_queryset(self):
        qs = super().get_queryset()
        param = self.forwarded.get("partner_entities", None)
        if param:
            qs = qs.filter(pk__in=param)
        return qs

    def get_result_label(self, result):
        return format_partner_entity(result)


class PartnershipPartnerRelationCompleteView(PartnerEntityAutocompleteView):
    """ Autocomplete used on partnership relation form"""

    def get_queryset(self):
        qs = super().get_queryset()
        param = self.forwarded.get("partnership", None)
        entities = PartnershipPartnerRelation.objects.filter(partnership=param).values_list('entity')
        if entities:
            qs = qs.filter(pk__in=entities)
        return qs

    def get_result_label(self, result):
        return format_partner_entity(result)
