from datetime import date

from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Q, Subquery

from base.models.entity import Entity
from base.models.entity_version import EntityVersion

__all__ = [
    'FacultyEntityAutocompleteView',
]


class FacultyEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Autocomplete for entities on UCLManagementEntity form
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Entity.objects.annotate(
            most_recent_acronym=Subquery(
                EntityVersion.objects
                    .filter(entity=OuterRef('pk'))
                    .order_by('-start_date')
                    .values('acronym')[:1]
            ),
            is_valid=Exists(
                EntityVersion.objects
                    .filter(entity=OuterRef('pk'))
                    .exclude(end_date__lte=date.today())
            )
        ).filter(is_valid=True)
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()

    def get_result_label(self, result):
        title = result.entityversion_set.latest("start_date").title
        return '{0.most_recent_acronym} - {1}'.format(result, title)
