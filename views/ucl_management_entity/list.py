from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import OuterRef, Q, Subquery
from django.views.generic import ListView

from partnership import perms
from base.models.entity_version import EntityVersion
from partnership.models import UCLManagementEntity
from partnership.utils import user_is_adri

__all__ = [
    'UCLManagementEntityListView'
]


class UCLManagementEntityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_list.html"
    context_object_name = "ucl_management_entities"
    login_url = 'access_denied'

    def test_func(self):
        return perms.user_can_list_ucl_management_entity(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_ucl_management_entity'] = perms.user_can_create_ucl_management_entity(
            self.request.user
        )
        return context

    def get_queryset(self):
        queryset = (
            UCLManagementEntity.objects
            .annotate(
                faculty_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('entity__entityversion__parent__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                entity_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('entity__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
            )
            .order_by('faculty_most_recent_acronym', 'entity_most_recent_acronym')
            .select_related(
                'academic_responsible',
                'administrative_responsible',
                'contact_in_person',
                'contact_out_person',
                'entity',
            )
        )
        if not user_is_adri(self.request.user):
            queryset = queryset.filter(Q(**{
                'entity__entityversion__parent'  # get faculty
                '__partnershipentitymanager__person__user': self.request.user,
            }) | Q(**{
                'entity__entityversion__parent'  # get faculty
                '__entityversion__parent'  # get sector
                '__partnershipentitymanager__person__user': self.request.user,
            }))
        return queryset.distinct()
