from django.db.models import Func, OuterRef, Subquery
from django.views.generic import ListView

from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY
from osis_role.contrib.views import PermissionRequiredMixin
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.auth.roles.partnership_manager import PartnershipEntityManager
from partnership.models import UCLManagementEntity

__all__ = [
    'UCLManagementEntityListView'
]


class UCLManagementEntityListView(PermissionRequiredMixin, ListView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_list.html"
    context_object_name = "ucl_management_entities"
    login_url = 'access_denied'
    permission_required = 'partnership.view_uclmanagemententity'

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
                    qs.filter(entity_type=FACULTY).values('acronym')[:1]
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
            .prefetch_related('entity__partnerships')
        )
        if not is_linked_to_adri_entity(self.request.user):
            # get what the user manages
            person = self.request.user.person
            entities_managed_by_user = PartnershipEntityManager.get_person_related_entities(person)

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
