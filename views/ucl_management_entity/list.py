from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Func, OuterRef, Subquery
from django.views.generic import ListView

from base.models.entity_version import EntityVersion
from partnership import perms
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
        cte = EntityVersion.objects.with_children()
        qs = cte.join(EntityVersion, id=cte.col.id).with_cte(cte).annotate(
            children=cte.col.children,
        ).filter(
            children__contains_any=OuterRef('entity__pk'),
        )

        queryset = (
            UCLManagementEntity.objects
            .annotate(
                faculty_most_recent_acronym=Subquery(
                    qs.filter(entity_type='FACULTY').values('acronym')[:1]
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
            # get what the user manages
            person = self.request.user.person
            entities_managed_by_user = person.partnershipentitymanager_set.values('entity_id')

            # get the children
            qs = cte.queryset().with_cte(cte).filter(
                entity__in=entities_managed_by_user
            ).annotate(
                child_entity_id=Func(cte.col.children, function='unnest'),
            ).distinct('child_entity_id').values('child_entity_id')

            # check if entity is part of entity the user manages
            queryset = queryset.filter(
                entity__in=qs,
            )
        return queryset.distinct()
