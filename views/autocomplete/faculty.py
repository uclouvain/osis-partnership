from datetime import date

from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Subquery

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
        last_version = EntityVersion.objects.filter(
            entity=OuterRef('pk')
        ).order_by('-start_date')

        qs = Entity.objects.annotate(
            most_recent_acronym=Subquery(last_version.values('acronym')[:1]),
            most_recent_title=Subquery(last_version.values('title')[:1]),
            is_valid=Exists(last_version.exclude(end_date__lte=date.today())),
        ).filter(is_valid=True)
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()

    def get_result_label(self, result):
        return '{0.most_recent_acronym} - {0.most_recent_title}'.format(result)
