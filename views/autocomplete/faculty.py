from datetime import date

from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Q, Subquery

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY
from partnership.utils import user_is_adri

__all__ = [
    'FacultyAutocompleteView',
    'FacultyEntityAutocompleteView',
]


class FacultyAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
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
                )
                .filter(entityversion__entity_type=FACULTY)
        )
        if not user_is_adri(self.request.user):
            qs = qs.filter(
                Q(partnershipentitymanager__person__user=self.request.user)
                | Q(entityversion__parent__partnershipentitymanager__person__user=self.request.user)
            )
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()

    def get_result_label(self, result):
        if result.entityversion_set:
            title = result.entityversion_set.latest("start_date").title
        else:
            return result.most_recent_acronym
        return '{0.most_recent_acronym} - {1}'.format(result, title)


class FacultyEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
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
        )
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(entityversion__parent=ucl_university)
        else:
            return Entity.objects.none()
        qs = qs.annotate(
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
