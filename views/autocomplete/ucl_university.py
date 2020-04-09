from django.db.models import Q

from .faculty import FacultyEntityAutocompleteView

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
            # entity has ucl management entity
            Q(uclmanagement_entity__isnull=False)
            # faculty of entity has ucl management entity
            | Q(entityversion__parent__uclmanagement_entity__isnull=False),
        )


class UclUniversityAutocompleteFilterView(FacultyEntityAutocompleteView):
    """
    Autocomplete for entities on partnership list filter form
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        return super().get_queryset().filter(partnerships__isnull=False)

    def get_result_label(self, result):
        if result.entityversion_set:
            title = result.entityversion_set.latest("start_date").title
        else:
            return result.most_recent_acronym
        return '{0.most_recent_acronym} - {1}'.format(result, title)
