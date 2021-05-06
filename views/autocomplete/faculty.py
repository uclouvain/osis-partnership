from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q

from base.models.enums.organization_type import MAIN

__all__ = [
    'FacultyEntityAutocompleteView',
]

from partnership.models import EntityProxy


class FacultyEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Autocomplete for entities on UCLManagementEntity form
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        # Get entities with their acronym_path
        qs = (
             EntityProxy.objects
             .only_valid()
             .with_title()
             .with_acronym_path()
             .with_path_as_string()
             .filter(organization__type=MAIN)
             .order_by('path_as_string')
        )

        if self.q:
            qs = qs.filter(
                Q(path_as_string__icontains=self.q)
                | Q(title__icontains=self.q)
            )
        return qs.distinct()

    def get_result_label(self, result):
        parts = result.acronym_path
        path = parts[1:] if len(parts) > 1 else parts
        return '{} - {}'.format(' / '.join(path), result.title)
