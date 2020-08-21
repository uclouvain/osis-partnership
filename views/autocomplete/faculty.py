from datetime import date

from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Q, Subquery, TextField

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.organization_type import MAIN
from base.utils.cte import CTESubquery

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

        # Get entities with their acronym_path
        qs = Entity.objects.annotate(
            most_recent_title=Subquery(last_version.values('title')[:1]),
            is_valid=Exists(last_version.exclude(end_date__lte=date.today())),
            path_as_string=CTESubquery(
                EntityVersion.objects.with_acronym_path(
                    entity_id=OuterRef('pk'),
                ).values('path_as_string')[:1],
                output_field=TextField()
            ),
            acronym_path=CTESubquery(
                EntityVersion.objects.with_acronym_path(
                    entity_id=OuterRef('pk'),
                ).values('acronym_path')[:1],
            ),
        ).filter(
            organization__type=MAIN,
            is_valid=True,
        ).order_by('path_as_string')

        if self.q:
            qs = qs.filter(
                Q(path_as_string__icontains=self.q)
                | Q(most_recent_title__icontains=self.q)
            )
        return qs.distinct()

    def get_result_label(self, result):
        parts = result.acronym_path
        path = parts[1:] if len(parts) > 1 else parts
        return '{} - {}'.format(' / '.join(path), result.most_recent_title)
