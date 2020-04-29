from django.db.models import OuterRef

from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY, SECTOR
from base.utils.cte import CTESubquery
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
        # Get entities with their sector and faculty (if exists)
        cte = EntityVersion.objects.with_children(entity_id=OuterRef('pk'))
        qs = cte.join(
            EntityVersion, id=cte.col.id
        ).with_cte(cte).order_by('-start_date')

        last_version = EntityVersion.objects.filter(
            entity=(OuterRef('pk'))
        ).order_by('-start_date')

        return super().get_queryset().filter(
            PartnershipForm.get_entities_condition(self.request.user)
        ).annotate(
            sector_acronym=CTESubquery(
                qs.filter(entity_type=SECTOR).values('acronym')[:1]
            ),
            faculty_acronym=CTESubquery(
                qs.exclude(
                    entity_id=(OuterRef('pk')),
                ).filter(entity_type=FACULTY).values('acronym')[:1]
            ),
            entity_title=CTESubquery(
                last_version.values('title')[:1]
            ),
        )

    def get_result_label(self, result):
        acronyms = filter(None, [
            result.sector_acronym,
            result.faculty_acronym,
            result.most_recent_acronym,
        ])
        return '{} - {}'.format(' / '.join(acronyms), result.entity_title)


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
