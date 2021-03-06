from partnership.models.enums.partnership import PartnershipType
from .faculty import FacultyEntityAutocompleteView
from ...forms import PartnershipMobilityForm

__all__ = [
    'UclUniversityAutocompleteFilterView',
    'UclEntityAutocompleteView',
]


class UclEntityAutocompleteView(FacultyEntityAutocompleteView):
    """
    Autocomplete for entities on Partnership form
    """
    def get_queryset(self):
        qs = super().get_queryset()
        if self.forwarded['partnership_type'] == PartnershipType.MOBILITY.name:
            qs = qs.filter(
                PartnershipMobilityForm.get_partnership_entities_managed(self.request.user)
            )
        return qs


class UclUniversityAutocompleteFilterView(FacultyEntityAutocompleteView):
    """
    Autocomplete for entities on partnership list filter form
    """
    def get_queryset(self):
        return super().get_queryset().ucl_entities()
