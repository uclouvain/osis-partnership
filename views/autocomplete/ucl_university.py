from .faculty import FacultyEntityAutocompleteView
from ...forms import PartnershipForm

__all__ = [
    'UclUniversityAutocompleteFilterView',
    'UclEntityAutocompleteView',
]


class UclEntityAutocompleteView(FacultyEntityAutocompleteView):
    """
    Autocomplete for entities on Partnership form
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        return super().get_queryset().filter(
            PartnershipForm.get_entities_condition(self.request.user)
        )


class UclUniversityAutocompleteFilterView(FacultyEntityAutocompleteView):
    """
    Autocomplete for entities on partnership list filter form
    """
    def get_queryset(self):
        return super().get_queryset().filter(partnerships__isnull=False)
