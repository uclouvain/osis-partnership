from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from base.models.academic_year import AcademicYear
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY, SECTOR
from base.utils.search import SearchMixin
from partnership import perms
from partnership.api.serializers import PartnershipAdminSerializer
from partnership.filter import PartnershipAdminFilter
from partnership.models import AgreementStatus, Partnership
from partnership.utils import user_is_adri, user_is_gf

__all__ = [
    'PartnershipsListView',
]


class PartnershipsListView(PermissionRequiredMixin, SearchMixin, FilterView):
    template_name = 'partnerships/partnership/partnership_list.html'
    context_object_name = 'partnerships'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'
    serializer_class = PartnershipAdminSerializer
    filterset_class = PartnershipAdminFilter
    cache_search = False

    def get(self, *args, **kwargs):
        if not self.request.GET and user_is_gf(self.request.user):
            university = self.request.user.person.partnershipentitymanager_set.first().entity
            if Partnership.objects.filter(ucl_entity=university).exists():
                return HttpResponseRedirect(
                    '?ucl_entity={0}'.format(university.pk)
                )
        return super().get(*args, **kwargs)

    def get_queryset(self):
        validity_end_year = Subquery(AcademicYear.objects.filter(
            partnership_agreements_end__partnership=OuterRef('pk'),
            partnership_agreements_end__status=AgreementStatus.VALIDATED.name,
        ).order_by('-end_date').values('year')[:1])
        ref = OuterRef('ucl_entity__pk')

        cte = EntityVersion.objects.with_children(entity_id=ref)
        qs = cte.join(EntityVersion, id=cte.col.id).with_cte(cte).order_by('-start_date')

        return (
            Partnership.objects
            .all()
            .select_related(
                'ucl_entity',
                'partner__contact_address__country', 'partner_entity',
                'supervisor',
            )
            .annotate(
                validity_end_year=validity_end_year,
                ucl_sector_most_recent_acronym=CTESubquery(
                    qs.filter(entity_type=SECTOR).values('acronym')[:1]
                ),
                ucl_sector_most_recent_title=CTESubquery(
                    qs.filter(entity_type=SECTOR).values('title')[:1]
                ),
                ucl_faculty_most_recent_acronym=CTESubquery(
                    qs.filter(
                        entity_type=FACULTY,
                    ).exclude(
                        entity_id=ref,
                    ).values('acronym')[:1]
                ),
                ucl_faculty_most_recent_title=CTESubquery(
                    qs.filter(
                        entity_type=FACULTY,
                    ).exclude(
                        entity_id=ref,
                    ).values('title')[:1]
                ),
                ucl_entity_most_recent_acronym=CTESubquery(
                    EntityVersion.objects
                        .filter(entity=ref)
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                ucl_entity_most_recent_title=CTESubquery(
                    EntityVersion.objects
                        .filter(entity=ref)
                        .order_by('-start_date')
                        .values('title')[:1]
                ),
            )
        ).distinct()

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context['can_change_configuration'] = user_is_adri(user)
        context['can_add_partnership'] = perms.user_can_add_partnership(user)
        context['url'] = reverse('partnerships:list')
        context['export_url'] = reverse('partnerships:export')
        context['search_button_label'] = _('search_partnership')
        return context

    def get_paginate_by(self, queryset):
        return 20
