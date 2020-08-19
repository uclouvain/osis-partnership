from datetime import date

from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Q, Subquery, F

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY, SECTOR
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

        # Get entities with their sector and faculty (if exists)
        cte = EntityVersion.objects.with_children(entity_id=OuterRef('pk'))
        qs = cte.join(
            EntityVersion, id=cte.col.id
        ).with_cte(cte).order_by('-start_date')

        qs = Entity.objects.annotate(
            most_recent_acronym=Subquery(last_version.values('acronym')[:1]),
            most_recent_title=Subquery(last_version.values('title')[:1]),
            is_valid=Exists(last_version.exclude(end_date__lte=date.today())),
            sector_acronym=CTESubquery(
                qs.filter(entity_type=SECTOR).values('acronym')[:1]
            ),
            faculty_acronym=CTESubquery(
                qs.exclude(
                    entity_id=(OuterRef('pk')),
                ).filter(entity_type=FACULTY).values('acronym')[:1]
            ),
        ).filter(
            is_valid=True,
            organization__type=MAIN,
        ).order_by(
            'sector_acronym',
            F('faculty_acronym').asc(nulls_first=True),
            'most_recent_acronym',
        )
        if self.q:
            qs = qs.filter(
                Q(most_recent_acronym__icontains=self.q)
                | Q(most_recent_title__icontains=self.q)
                | Q(sector_acronym__icontains=self.q)
                | Q(faculty_acronym__icontains=self.q)
            )
        return qs.distinct()

    def get_result_label(self, result):
        acronyms = filter(None, [
            result.sector_acronym,
            result.faculty_acronym,
            result.most_recent_acronym,
        ])
        return '{} - {}'.format(' / '.join(acronyms), result.most_recent_title)
