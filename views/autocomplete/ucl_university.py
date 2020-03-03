from datetime import date

from django.db.models import Exists, OuterRef, Subquery

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from .faculty import FacultyAutocompleteView, FacultyEntityAutocompleteView

__all__ = [
    'UclUniversityAutocompleteView',
    'UclUniversityAutocompleteFilterView',
    'UclUniversityLaboAutocompleteView',
    'UclUniversityLaboAutocompleteFilterView',
]


class UclUniversityAutocompleteView(FacultyAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        return super().get_queryset().filter(faculty_managements__isnull=False)


class UclUniversityLaboAutocompleteView(FacultyEntityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        return super().get_queryset().filter(entity_managements__isnull=False)


class UclUniversityAutocompleteFilterView(UclUniversityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = (
            Entity.objects
            .annotate(
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
                ),
            )
            .filter(partnerships__isnull=False, is_valid=True)
        )
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()


class UclUniversityLaboAutocompleteFilterView(UclUniversityLaboAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = super().get_queryset()
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(partnerships_labo__ucl_university=ucl_university)
        else:
            return Entity.objects.none()
        return qs.distinct()
